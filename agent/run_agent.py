"""Run a local model as a Remotion agent, the way Bionic does, and log everything.

The model gets the skill as system prompt and the same tools Bionic exposes:
filesystem tools (same schema as @modelcontextprotocol/server-filesystem, limited
to the Remotion project) plus the remotion-check tools.

Usage: uv run --project ../remotion-check python run_agent.py "<user prompt>" [--model ID] [--log FILE]
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "remotion-check"))
import server as check  # noqa: E402

PROJECT = check.PROJECT
SKILL = ROOT / "skills" / "remotion-video" / "SKILL.md"


def inside(path: str) -> Path:
    p = (PROJECT / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if p != PROJECT.resolve() and PROJECT.resolve() not in p.parents:
        raise ValueError(f"Access denied: {p} is outside {PROJECT}")
    return p


def read_text_file(path: str, head: int | None = None, tail: int | None = None) -> str:
    lines = inside(path).read_text().splitlines()
    if head:
        lines = lines[:head]
    if tail:
        lines = lines[-tail:]
    return "\n".join(lines)


def write_file(path: str, content: str) -> str:
    p = inside(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Successfully wrote to {path}"


def edit_file(path: str, edits: list[dict], dryRun: bool = False) -> str:
    p = inside(path)
    text = p.read_text()
    for e in edits:
        if e["oldText"] not in text:
            raise ValueError(f"Could not find exact match for edit:\n{e['oldText']}")
        text = text.replace(e["oldText"], e["newText"], 1)
    if not dryRun:
        p.write_text(text)
    return f"Applied {len(edits)} edit(s) to {path}"


def list_directory(path: str) -> str:
    return "\n".join(f"[{'DIR' if c.is_dir() else 'FILE'}] {c.name}" for c in sorted(inside(path).iterdir()))


def create_directory(path: str) -> str:
    inside(path).mkdir(parents=True, exist_ok=True)
    return f"Successfully created directory {path}"


S = {"type": "string"}
TOOLS = {
    "read_text_file": (read_text_file, "Read a text file.", {"path": S, "head": {"type": "number"}, "tail": {"type": "number"}}, ["path"]),
    "write_file": (write_file, "Create or overwrite a file.", {"path": S, "content": S}, ["path", "content"]),
    "edit_file": (edit_file, "Line-based edits: replace exact text sequences.", {
        "path": S, "dryRun": {"type": "boolean"},
        "edits": {"type": "array", "items": {"type": "object", "properties": {"oldText": S, "newText": S},
                                              "required": ["oldText", "newText"]}}}, ["path", "edits"]),
    "list_directory": (list_directory, "List a directory.", {"path": S}, ["path"]),
    "create_directory": (create_directory, "Create a directory.", {"path": S}, ["path"]),
    "check_code": (check.check_code, check.check_code.__doc__, {"folder": S}, ["folder"]),
    "describe_media": (check.describe_media, check.describe_media.__doc__, {"path": S}, ["path"]),
    "review_frames": (check.review_frames, check.review_frames.__doc__, {
        "composition": S, "frames": {"type": "array", "items": {"type": "integer"}}, "brief": S}, ["composition"]),
    "render_video": (check.render_video, check.render_video.__doc__, {"composition": S}, ["composition"]),
}
SCHEMA = [{"type": "function", "function": {"name": n, "description": d,
           "parameters": {"type": "object", "properties": props, "required": req}}}
          for n, (_, d, props, req) in TOOLS.items()]


def replay(path: Path) -> list[dict]:
    """Rebuild assistant and tool messages from a log, dropping a trailing empty answer."""
    out: list[dict] = []
    pending: list[str] = []
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if "message" in row:
            m = row["message"]
            if not m.get("tool_calls"):
                continue
            out.append({k: v for k, v in m.items() if k in ("role", "content", "reasoning_content", "tool_calls")})
            pending = [c["id"] for c in m["tool_calls"]]
        else:
            out.append({"role": "tool", "tool_call_id": pending.pop(0), "content": row["result"]})
    return out


KEEP_RECENT = 6  # assistant turns kept verbatim


def compact(messages: list[dict]) -> int:
    """Shrink old history in place; returns how many messages changed.

    What fills the context is not the conversation but its payloads: full file contents in
    write_file/edit_file calls, file reads, reviews, and reasoning. Old ones are replaced by
    short notes: the files are on disk, PLAN.md holds the plan. Old assistant turns lose
    their text and reasoning together (keeping text without reasoning confuses the template).
    """
    assistant_idx = [i for i, m in enumerate(messages) if m["role"] == "assistant"]
    if len(assistant_idx) <= KEEP_RECENT:
        return 0
    cutoff = assistant_idx[-KEEP_RECENT]
    changed = 0
    for m in messages[2:cutoff]:
        if m["role"] == "assistant":
            if m.get("content") or m.get("reasoning_content"):
                m["content"] = ""
                m.pop("reasoning_content", None)
                changed += 1
            for call in m.get("tool_calls") or []:
                fn = call["function"]
                if fn["name"] in ("write_file", "edit_file") and len(fn["arguments"]) > 300:
                    try:
                        path = json.loads(fn["arguments"]).get("path", "?")
                    except json.JSONDecodeError:
                        path = "?"
                    fn["arguments"] = json.dumps({"path": path, "note": "content omitted to save context; read the file if needed"})
                    changed += 1
        elif m["role"] == "tool" and len(m.get("content") or "") > 400:
            m["content"] = m["content"][:300] + "\n[... older tool output shortened to save context]"
            changed += 1
    return changed


def video_folder(messages: list[dict]) -> Path | None:
    """The composition folder the agent is working on: the last src/<Name>/ it wrote to."""
    for m in reversed(messages):
        for call in m.get("tool_calls") or []:
            found = re.search(r"src/([A-Za-z0-9_]+)/", call["function"]["arguments"])
            if found and found.group(1) != "kit" and (PROJECT / "src" / found.group(1)).is_dir():
                return PROJECT / "src" / found.group(1)
    return None


def workspace_map(folder: Path) -> str:
    """What exists on disk, in a few lines per file: exports, local imports, size. After compaction
    this replaces re-reading every file to remember what was written."""
    lines = [f"[WORKSPACE MAP: generated from disk, current] {folder.relative_to(PROJECT)}/"]
    for f in sorted(folder.iterdir()):
        if not f.is_file():
            continue
        text = f.read_text(errors="replace")
        if f.suffix == ".md":
            lines.append(f"- {f.name} ({len(text.splitlines())} lines)")
            continue
        exports = re.findall(r"export\s+(?:const|function|type|interface)\s+(\w+)", text)
        local = re.findall(r"import\s*\{([^}]*)\}\s*from\s*[\"']\./(\w+)[\"']", text)
        imports = "; ".join(f"{', '.join(x.strip() for x in names.split(','))} from ./{src}" for names, src in local)
        lines.append(f"- {f.name} ({len(text.splitlines())} lines) exports: {', '.join(exports) or '-'}"
                     + (f" | imports: {imports}" if imports else ""))
    timeline = re.findall(r"\{\s*len:\s*(\d+)\s*,\s*Comp:\s*(\w+)\s*\}", (folder / "index.tsx").read_text(errors="replace")) \
        if (folder / "index.tsx").exists() else []
    if timeline:
        lines.append("Timeline: " + " → ".join(f"{c} {n}f" for n, c in timeline))
    lines.append("Old file contents were removed from this chat to save context. Trust this map and PLAN.md; "
                 "read a file only to edit it. To find broken imports or types, run check_code instead of reading.")
    return "\n".join(lines)


def loaded_context(model: str) -> int:
    try:
        for m in httpx.get(f"{check.LMSTUDIO}/api/v0/models", timeout=10).json()["data"]:
            if m["id"] == model and m.get("state") == "loaded":
                return int(m.get("loaded_context_length") or 0) or 49152
    except Exception:
        pass
    return 49152


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--model", default="qwen_qwen3.6-27b")
    ap.add_argument("--log", default="run.jsonl")
    ap.add_argument("--max-steps", type=int, default=80)
    ap.add_argument("--resume", help="continue the conversation stored in a previous log")
    ap.add_argument("--effort", choices=["none", "low", "medium", "high"],
                    help="reasoning effort (LM Studio reasoning_effort); default: the model's own")
    args = ap.parse_args()
    check.OPEN_VIDEO = False
    check.ORIGINAL_BRIEF = args.prompt  # fidelity is checked against the real prompt, not a paraphrase
    system = (f"Allowed directory for the filesystem tools: {PROJECT}\n\n"
              f"Skill loaded for this task:\n\n{SKILL.read_text()}")
    messages = [{"role": "system", "content": system}, {"role": "user", "content": args.prompt}]
    if args.resume:
        messages += replay(Path(args.resume))
    log = open(args.log, "w")
    t0 = time.monotonic()
    ctx_limit = loaded_context(args.model)
    nudges = trims = early_ends = 0
    need_map = False
    for step in range(args.max_steps):
        folder = video_folder(messages) if need_map else None
        if folder:
            for m in messages:  # keep only the newest map
                if m["role"] == "user" and m["content"].startswith("[WORKSPACE MAP"):
                    m["content"] = "[older workspace map removed]"
            messages.append({"role": "user", "content": workspace_map(folder)})
            need_map = False
        if step == args.max_steps - 15:
            messages.append({"role": "user", "content": (
                "Only 15 steps left in this session. Stop polishing: fix only what breaks the render, "
                "run check_code, then render_video, then write your report.")})
            print("    (15 steps left: told the agent to wrap up)", flush=True)
        r = httpx.post(f"{check.LMSTUDIO}/v1/chat/completions", timeout=3600, json={
            "model": args.model, "messages": messages, "tools": SCHEMA,
            **({"reasoning_effort": args.effort} if args.effort else {})})
        if r.status_code >= 400:
            # Usually the prompt no longer fits: compact harder and try once more
            global KEEP_RECENT
            KEEP_RECENT = 2
            print(f"    (LM Studio error {r.status_code}: compacted {compact(messages)} messages, retrying)", flush=True)
            r = httpx.post(f"{check.LMSTUDIO}/v1/chat/completions", timeout=3600, json={
                "model": args.model, "messages": messages, "tools": SCHEMA,
            **({"reasoning_effort": args.effort} if args.effort else {})})
        r.raise_for_status()
        data = r.json()
        msg = data["choices"][0]["message"]
        usage = data.get("usage", {})
        if usage.get("prompt_tokens", 0) > 0.6 * ctx_limit:
            n = compact(messages)
            if n:
                print(f"    (context {usage['prompt_tokens'] // 1000}k of {ctx_limit // 1000}k: compacted {n} old messages)", flush=True)
                need_map = True
        if data["choices"][0].get("finish_reason") == "length" and not msg.get("tool_calls") and trims < 3:
            # The reply was cut by the context limit: drop old tool outputs (like Bionic's
            # "truncate middle" overflow policy) and ask again, instead of ending the run.
            trims += 1
            tools_seen = [m for m in messages if m["role"] == "tool"]
            for m in tools_seen[:-6]:
                m["content"] = "[old tool output removed to free context]"
            print(f"    (reply cut by context limit: trimmed old tool outputs, retry {trims})", flush=True)
            continue
        messages.append({k: v for k, v in msg.items() if k in ("role", "content", "reasoning_content", "tool_calls")})
        log.write(json.dumps({"step": step, "t": round(time.monotonic() - t0), "usage": usage, "message": msg}) + "\n")
        log.flush()
        print(f"[{step}] {time.monotonic() - t0:.0f}s ctx={usage.get('prompt_tokens')} "
              f"tools={[c['function']['name'] for c in msg.get('tool_calls') or []]}", flush=True)
        rendered = any(m["role"] == "tool" and m["content"].startswith("Video ready:") for m in messages)
        if not msg.get("tool_calls") and not rendered and early_ends < 3 and step < args.max_steps - 2:
            # Ended without a video: usually a reasoning budget cut mid-thought, not a real conclusion
            early_ends += 1
            messages.append({"role": "user", "content": (
                "The video is not rendered yet, so the work isn't finished. Re-read PLAN.md if needed and "
                "continue with the next step of the method: finish the scenes, check_code, review_frames, "
                "render_video. Keep each thought short: decide, then act.")})
            print(f"    (ended without a video: sent back to work, {early_ends}/3)", flush=True)
            continue
        if not msg.get("tool_calls"):
            if not (msg.get("content") or "").strip() and nudges < 2:
                # The model ended its turn silently: do what a user would do in Bionic
                nudges += 1
                messages.append({"role": "user", "content": "continua"})
                print(f"    (empty turn: nudge {nudges} sent)", flush=True)
                continue
            print(f"\nFINAL ANSWER (nudges: {nudges}):\n" + (msg.get("content") or ""))
            break
        for call in msg["tool_calls"]:
            name = call["function"]["name"]
            try:
                fn = TOOLS[name][0]
                result = str(fn(**json.loads(call["function"]["arguments"] or "{}")))
            except Exception as e:
                result = f"Error: {e}"
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})
            log.write(json.dumps({"step": step, "tool": name, "args": call["function"]["arguments"][:400],
                                  "result": result}) + "\n")
            log.flush()
            print(f"    {name} -> {result[:160]!r}", flush=True)


if __name__ == "__main__":
    main()
