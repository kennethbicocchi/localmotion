"""remotion-check MCP server: gives a local model the checks and the eyes it lacks.

Tools: check_code, describe_media, review_frames, render_video.
Everything runs inside PROJECT only.
"""
import base64
import io
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import httpx
from PIL import Image as Pil, ImageChops, ImageDraw, ImageFilter, ImageOps, ImageStat
from mcp.server.mcpserver import MCPServer

BASE = Path(__file__).parent
# The Remotion project the agent works in: REMOTION_PROJECT, or the template shipped with this repo
PROJECT = Path(os.environ.get("REMOTION_PROJECT", BASE.parent / "remotion-template")).expanduser().resolve()
SRC = PROJECT / "src"
PUBLIC = PROJECT / "public"
CHECK_DIR = PROJECT / "out" / "check"
LMSTUDIO = os.environ.get("LMSTUDIO_URL", "http://127.0.0.1:1234")
SCALE = 0.5               # review frames at half resolution
AUTO_FRAMES = 8           # frames picked automatically
MOTION_GAP = 30           # compare f with f+30 (1 s) to spot frames where nothing moves
MAX_REVIEWS = 4           # review_frames calls per composition before it refuses
OPEN_VIDEO = True         # open the finished video in the default player
IMAGES = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO = {".mp3", ".wav", ".m4a", ".ogg", ".aac"}
VIDEO = {".mp4", ".mov", ".webm", ".mkv"}
_reviews: dict[str, int] = {}

mcp = MCPServer("remotion-check")


def run(cmd: list[str], timeout: int = 300) -> tuple[int, str]:
    """Run a command in the project; return (exit code, stdout+stderr)."""
    try:
        p = subprocess.run(cmd, cwd=PROJECT, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        return 124, f"Timed out after {timeout} s: {' '.join(cmd)}"


def src_folder(folder: str) -> Path:
    d = (SRC / folder.strip().strip("/").removeprefix("src/")).resolve()
    if SRC.resolve() not in d.parents:
        raise ValueError(f"The folder must be inside {SRC}.")
    return d


# ---------------------------------------------------------------- vision

def vision_model() -> str | None:
    """Id of the first vision model already loaded in LM Studio, or None."""
    try:
        models = httpx.get(f"{LMSTUDIO}/api/v0/models", timeout=10).json()["data"]
    except Exception:
        return None
    for m in models:
        if m.get("state") == "loaded" and m.get("type") == "vlm":
            return m["id"]
    return None


def to_jpeg_b64(source: Path | Pil.Image, side: int) -> str:
    img = source if isinstance(source, Pil.Image) else ImageOps.exif_transpose(Pil.open(source))
    img = img.convert("RGB")
    img.thumbnail((side, side))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode()


def ask_vision(images: list[tuple[str, Path | Pil.Image]], instructions: str,
               side: int = 960, max_tokens: int = 8000, effort: str = "low") -> str:
    model = vision_model()
    if model is None:
        return "VISION UNAVAILABLE: no vision model is loaded in LM Studio. The automatic checks still apply."
    content: list[dict] = []
    for label, source in images:
        if label:
            content.append({"type": "text", "text": label})
        content.append({"type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{to_jpeg_b64(source, side)}"}})
    content.append({"type": "text", "text": instructions})
    try:
        r = httpx.post(f"{LMSTUDIO}/v1/chat/completions", timeout=900, json={
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": max_tokens,
            "temperature": 0.3,
            # Judging what is visible needs little reasoning: unbounded thinking used to eat the whole
            # budget and return nothing. LM Studio honors reasoning_effort (not enable_thinking).
            "reasoning_effort": effort,
        })
        r.raise_for_status()
        text = (r.json()["choices"][0]["message"].get("content") or "").strip()
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
        return text or "The vision model returned no answer."
    except Exception as e:
        return f"VISION UNAVAILABLE ({e})."


# ---------------------------------------------------------------- check_code

# (pattern, message). ERRORS break the render or the result.
ERRORS = [
    (r"Math\.random\(", "Math.random() changes on every render: use random('seed') imported from remotion."),
    (r"\buse(State|Effect|LayoutEffect)\b|setTimeout|setInterval|requestAnimationFrame",
     "No state, effects or timers: every animated value is computed from useCurrentFrame()."),
    (r"transition\s*:\s*[\"'`]|animation\s*:\s*[\"'`]|@keyframes|className=[\"'][^\"']*\b(animate-|transition)",
     "CSS animations and Tailwind animate-/transition classes are not rendered: use interpolate/spring."),
    (r"<img[\s>]", "Use <Img> from remotion (or the kit's <Photo>), not <img>: <img> may not be loaded at render time."),
    (r"<video[\s>]", "Use <OffthreadVideo> from remotion, not <video>."),
    (r"<audio[\s>]", "Use <Audio> from remotion, not <audio>."),
    (r"staticFile\([\"'`](/|public/)",
     "staticFile takes the path inside public/ without 'public/' and without a leading '/': staticFile(\"folder/photo.jpg\")."),
    (r"src=[\"'{]+[\"'`]?/(?!/)", "Local files are loaded with staticFile(\"folder/file\"), not with a path starting with '/'."),
    (r"(?i)lorem ipsum", "Placeholder text: write the real copy."),
    (r"fontFamily:\s*[\"'`](Arial|Helvetica|Georgia|Times|Verdana|Tahoma|Impact|Courier|sans-serif|serif|monospace|system-ui)",
     "System font: load fonts with the kit's loadType() in theme.ts and use type.display / type.body / type.detail."),
]
WARNINGS = [
    (r"objectFit:\s*[\"']contain",
     "objectFit 'contain' leaves empty bands: for photos use the kit's <Photo> (fills the box, centers the subject)."),
    (r"[\U0001F300-\U0001FAFF☀-⛿]",
     "Emoji in the video look amateurish and differ between systems. Use SVG shapes or text."),
    (r"[\"'`][^\"'`\n]*&(gt|lt|amp|apos|quot|nbsp);[^\"'`\n]*[\"'`]",
     "HTML entity inside a JavaScript string: it shows up literally on screen (\"&gt;&gt;\" instead of \">>\"). "
     "Write the character itself inside strings; entities only work in JSX text between tags."),
    (r"fontSize:\s*(1\d|2\d|3[01])\b",
     "Text under 32 px is unreadable on a phone at 1080x1920. Minimum 40 px for text, 32 px only for minor labels."),
]


def spring_calls(text: str):
    """Yield (line, arguments) for every spring(...) call."""
    for m in re.finditer(r"\bspring\(", text):
        i, depth = m.end(), 1
        while i < len(text) and depth:
            depth += {"(": 1, ")": -1}.get(text[i], 0)
            i += 1
        yield text.count("\n", 0, m.start()) + 1, text[m.end():i]


def static_checks(d: Path) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    files = sorted(p for p in d.rglob("*") if p.suffix in {".ts", ".tsx"})
    uses_kit = False
    for f in files:
        rel = f.relative_to(PROJECT)
        text = f.read_text(errors="replace")
        uses_kit |= bool(re.search(r"from\s+[\"']\.\./kit[\"'/]", text))
        lines = text.splitlines()
        for rules, dest in ((ERRORS, errors), (WARNINGS, warnings)):
            for pattern, msg in rules:
                hits = [n for n, line in enumerate(lines, 1) if re.search(pattern, line)]
                if hits:
                    dest.append(f"{rel}:{','.join(map(str, hits[:6]))} — {msg}")
        for line, args in spring_calls(text):
            if not re.search(r"\bfps\b", args):
                errors.append(f"{rel}:{line} — spring() without fps: pass fps from useVideoConfig().")
            elif re.search(r"\bfps\s*:\s*\d", args):
                warnings.append(f"{rel}:{line} — hardcoded fps in spring(): use const {{ fps }} = useVideoConfig().")
    timing = {name: length for name, _, length in scene_timeline(d.name)}
    for f in files:
        text = f.read_text(errors="replace")
        rel = f.relative_to(PROJECT)
        # Ranges whose start grows with a loop index while the end is fixed crash once start >= end
        for m in re.finditer(r"interpolate\(\s*\w+\s*,\s*\[([^,\]]*\b[ijk]\b[^,\]]*),\s*(\d+)\s*\]", text):
            errors.append(f"{rel}:{text.count(chr(10), 0, m.start()) + 1} — interpolate range [{m.group(1).strip()}, "
                          f"{m.group(2)}]: the start grows with the loop index but the end is fixed, so it crashes "
                          "('inputRange must be strictly monotonically increasing') once start >= end. Make both "
                          "ends move with the index: [start + i * k, start + i * k + duration].")
        slow, stagger, ends = [], [], []
        for m in re.finditer(r"(?:prog\(\s*frame\s*,\s*|interpolate\(\s*frame\s*,\s*\[\s*)(\d+)\s*,\s*(\d+)", text):
            a, b = int(m.group(1)), int(m.group(2))
            if a > 0:
                ends.append(b)
                if b - a > 45:
                    slow.append(text.count("\n", 0, m.start()) + 1)
        ends += [int(x) + 20 for x in re.findall(r"delay(?:=\{|:\s*)(\d+)", text)]
        for m in re.finditer(r"\b[ijk]\s*\*\s*(\d+)", text):
            if int(m.group(1)) >= 6 and re.search(r"delay|frame|\[", text[max(0, m.start() - 40):m.start()]):
                stagger.append(text.count("\n", 0, m.start()) + 1)
        if slow:
            warnings.append(f"{rel}:{','.join(map(str, slow[:6]))} — slow animation (longer than 45 frames): entrances "
                            "take 10-20 frames, a whole build at most 30-45. Only background drift may be slow.")
        if stagger:
            warnings.append(f"{rel}:{','.join(map(str, stagger[:6]))} — fixed per-item stagger of 6+ frames: with many "
                            "items the build gets slow. Spread a fixed total instead: delay = stagger(i, count) from the kit.")
        length = timing.get(f.stem)
        if length and ends and max(ends) > length - 30:
            warnings.append(f"{rel} — the last animation lands around frame {max(ends)} of {length}: no breathing room. "
                            "Let the last element land at least 30 frames (1 s) before the scene ends.")
        if re.search(r"(?i)>[^<]*\bsource\b|[\"'](?:source|fonte)\s*:", text):
            warnings.append(f"{rel} — on-screen 'source' line: cite a source only if the user gave it to you. Every number "
                            "on screen must come from the brief or be a fact you are certain of.")
    sources = {f: f.read_text(errors="replace") for f in files}
    for f in files:
        if f.name in ("index.tsx", "theme.ts"):
            continue
        if not any(re.search(rf"from\s+[\"']\./{re.escape(f.stem)}[\"']", s) for g, s in sources.items() if g != f):
            warnings.append(f"{f.relative_to(PROJECT)} is not imported anywhere: delete it or add it to the timeline.")
    if files and not uses_kit:
        warnings.append(f"No file in {d.relative_to(PROJECT)} imports from \"../kit\": use Photo, RevealLine, "
                        "makeTimeline, loadType... instead of rewriting them (see the skill).")
    index = d / "index.tsx"
    if index.exists():
        t = index.read_text(errors="replace")
        if "<Composition" not in t:
            errors.append(f"{index.relative_to(PROJECT)} — no <Composition>: index.tsx must export the composition.")
        if re.search(r"durationInFrames=\{\s*\d+\s*\}", t) and "makeTimeline" in t:
            warnings.append(f"{index.relative_to(PROJECT)} — hardcoded Composition duration: use timeline.duration.")
    else:
        errors.append(f"Missing {d.relative_to(PROJECT)}/index.tsx with the <Composition>.")
    root = (SRC / "Root.tsx").read_text(errors="replace")
    if not re.search(rf"from\s+[\"']\./{re.escape(d.name)}(/index)?[\"']", root):
        errors.append(f"src/Root.tsx does not import ./{d.name}: add the import and the component inside "
                      "RemotionRoot with edit_file, without removing the other compositions.")
    return errors, warnings


CODE_LIKE = re.compile(r"^[\w./@-]+\.(tsx?|jsx?|css|png|jpe?g|mp3|mp4|svg|webp)$|^#[0-9a-f]{3,8}$|^\d+(px|em|%|deg|s|ms)?$|"
                       r"^(rgba?|hsla?|linear|radial|translate|scale|rotate|cubic|url)\(|^[a-z]+([A-Z][a-z]+)+$|^[a-z-]+$")


CSS_LIKE = re.compile(r"\d(px|em|rem|deg|ms|vh|vw)\b|rgba?\(|hsla?\(|gradient|var\(|calc\(|cubic-bezier|"
                      r"(brightness|saturate|contrast|blur|grayscale|sepia|hue-rotate|drop-shadow|opacity|invert)\(|"
                      r"^\s*[\d.\s%-]+$|^(solid|dashed|auto|none|inherit|absolute|relative|center|flex|block)\b")


def on_screen_text(d: Path) -> tuple[str, str]:
    """Approximate on-screen copy of a composition: (JSX text nodes and word-like string literals,
    numbers passed as props such as counters' to={40}: they may or may not be visible)."""
    parts, props = [], []
    for f in sorted(d.glob("*.tsx")) + sorted(d.glob("*.ts")):
        src = re.sub(r"^\s*(import|export \* from).*$", "", f.read_text(errors="replace"), flags=re.M)
        src = re.sub(r"//[^\n]*|/\*.*?\*/", "", src, flags=re.S)
        for m in re.finditer(r">\s*([^<>{}]*[A-Za-z0-9][^<>{}]*?)\s*</", src):
            parts.append("\u2063" + m.group(1))  # marker: JSX text is on screen even if it's only a number
        for m in re.finditer(r"\"([^\"\n]{1,200})\"|'([^'\n]{1,200})'|`([^`$\n]{1,200})`", src):
            s = next(g for g in m.groups() if g is not None).strip()
            if re.search(r"[A-Za-z]", s) and not CODE_LIKE.match(s) and not CSS_LIKE.search(s) and " " in s or \
                    re.fullmatch(r"[A-Z0-9][A-Z0-9 '&.,!?:+%-]{1,60}", s or "-"):
                parts.append(s)
        for m in re.finditer(r"\b(?:text|label|title|caption|word)\s*[:=]\s*[\"'`](\d[\d.,]*)[\"'`]", src):
            parts.append("\u2063" + m.group(1))  # numbers given as on-screen text props: { text: "3" }
        for m in re.finditer(r"\b(?:to|value|count|number|amount|target)\s*[:=]\s*\{?\s*(\d[\d.]*)", src):
            props.append(m.group(1))
    text = " ".join(p.lstrip("\u2063") for p in parts if p.startswith("\u2063") or not re.fullmatch(r"[\d.\s%]+", p))
    return text, " ".join(props)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w%+]+", " ", s.lower())).strip()


NUMBER = re.compile(r"(?<![\w.])\d[\d.,]*(?:\s?(?:%|[kKmMbB]\b|\+))?")


ORIGINAL_BRIEF: str | None = None  # set by a host that knows the user's exact prompt (agent loop, bot)


def fidelity(d: Path) -> list[str]:
    """Compare the composition with the user's request: the exact prompt when the host knows it,
    otherwise BRIEF.md (which the model is asked to save verbatim)."""
    brief_file = d / "BRIEF.md"
    if ORIGINAL_BRIEF:
        brief = ORIGINAL_BRIEF
    elif brief_file.exists():
        brief = brief_file.read_text(errors="replace")
    else:
        return [f"Missing {brief_file.relative_to(PROJECT)}: save the user's request there verbatim, "
                "so the video can be checked against it."]
    screen, props = on_screen_text(d)
    notes = []
    key = lambda n: re.sub(r"[\s,.+]", "", n.lower())
    brief_numbers = {key(n): n.strip() for n in NUMBER.findall(brief)}
    screen_numbers = {key(n): n.strip() for n in NUMBER.findall(screen)}
    duration = re.search(r"(\d+)\s*(?:-|\u2013)?\s*(?:s\b|sec|second|secondi)", brief, re.I)
    ignore = {key(duration.group(1)), str(int(duration.group(1)) * 30)} if duration else set()  # seconds and frames
    ignore |= {k for k in brief_numbers if re.fullmatch(r"\d{3,4}x\d{3,4}|1080|1920|720|30|60|9|16", k)}
    visible_or_props = set(screen_numbers) | {key(n) for n in NUMBER.findall(props)}
    missing = [v for k, v in brief_numbers.items()
               if k not in visible_or_props and re.sub(r"[a-z%]", "", k) not in visible_or_props and k not in ignore]
    # Only numbers that read like claims: amounts with a unit, percentages, years. HUD readouts are fine.
    claim = re.compile(r"\d+(?:[.,]\d+)?\s?(?:%|[kKmMbB]|\+)$|^(?:1[89]|20)\d\d$")
    added = [v for k, v in screen_numbers.items()
             if k not in brief_numbers and claim.search(v)
             and not ("," in v and not re.fullmatch(r"\d{1,3}(,\d{3})+", v))]  # skip color tuples like 230,0,18
    if missing:
        notes.append("Numbers in the brief that are not on screen: " + ", ".join(missing[:10]) +
                     ". The user's figures must appear (unless they're only a format or duration).")
    if added:
        notes.append("Numbers on screen that are not in the brief: " + ", ".join(added[:10]) +
                     ". Keep them only if they're facts you're certain of, never invented statistics; if the user "
                     "gave a script, don't add figures to it.")
    screen_n = norm(screen)
    for quote in re.findall(r"[\"\u201c\u00ab]([^\"\u201d\u00bb\n]{12,200})[\"\u201d\u00bb]", brief):
        words = [w for w in norm(quote).split() if len(w) > 2 or w.isdigit()]
        if len(quote.split()) >= 3 and norm(quote) not in screen_n and not all(w in screen_n.split() for w in words):
            notes.append(f'Quoted text from the brief not found on screen: "{quote[:80]}". Use the user\'s exact words.')
    index = d / "index.tsx"
    if index.exists():
        idx = index.read_text(errors="replace")
        w, h = re.search(r"width=\{(\d+)\}", idx), re.search(r"height=\{(\d+)\}", idx)
        if w and h:
            vertical = int(h.group(1)) > int(w.group(1))
            # An explicit ratio wins over words like "vertical", which may describe something inside the video
            ratio = re.search(r"\b(16:9|9:16|1920\s*x\s*1080|1080\s*x\s*1920)\b", brief)
            if ratio:
                wants_vertical = ratio.group(1).startswith("9:16") or ratio.group(1).startswith("1080")
            elif re.search(r"\b(horizontal|orizzontale|landscape)\b", brief, re.I):
                wants_vertical = False
            elif re.search(r"\b(vertical|verticale|reel|story|tiktok)\b", brief, re.I):
                wants_vertical = True
            else:
                wants_vertical = None
            if wants_vertical is not None and wants_vertical != vertical:
                notes.append(f"The brief asks for a {'vertical' if wants_vertical else 'horizontal'} video but the "
                             f"composition is {'vertical' if vertical else 'horizontal'}.")
        timeline = scene_timeline(d.name)
        total = sum(length for _, _, length in timeline)
        if duration and total:
            want = int(duration.group(1)) * 30
            if abs(total - want) > 0.1 * want:
                notes.append(f"Duration: the brief asks for {duration.group(1)} s, the timeline lasts {total / 30:.1f} s.")
    return notes


def tsc_errors(d: Path) -> tuple[list[str], int]:
    _, out = run(["npx", "--no-install", "tsc", "--noEmit", "--pretty", "false"], timeout=240)
    mine, others = [], 0
    my_paths = (str(d.relative_to(PROJECT)) + "/", "src/Root.tsx", "src/kit/")
    for line in out.splitlines():
        if ": error TS" not in line:
            continue
        if line.startswith(my_paths):
            mine.append(line.strip())
        else:
            others += 1
    return mine, others


def eslint_errors(d: Path) -> list[str]:
    _, out = run(["npx", "--no-install", "eslint", "--format", "json", str(d.relative_to(PROJECT))], timeout=180)
    try:
        data = json.loads(out[out.index("["):])
    except Exception:
        return []
    lines = []
    for f in data:
        rel = Path(f["filePath"]).relative_to(PROJECT)
        for m in f["messages"]:
            if m.get("severity") == 2:
                lines.append(f"{rel}:{m.get('line', '?')} — {m['message']} ({m.get('ruleId')})")
    return lines


@mcp.tool()
def check_code(folder: str) -> str:
    """Check a composition's code: TypeScript, ESLint and the typical Remotion mistakes.

    folder: the composition's folder inside src/, for example "LaunchTrailer".
    Run it after every change, before review_frames. Fix every ERROR and run it
    again until it answers "NO ERRORS".
    """
    try:
        d = src_folder(folder)
    except ValueError as e:
        return str(e)
    if not d.is_dir():
        present = ", ".join(sorted(p.name for p in SRC.iterdir() if p.is_dir()))
        return f"The folder src/{folder} does not exist. Existing folders: {present}."
    static, warnings = static_checks(d)
    tsc, others = tsc_errors(d)
    errors = tsc + eslint_errors(d) + static
    parts = []
    if errors:
        parts.append(f"ERRORS ({len(errors)}), fix all of them:\n" + "\n".join(f"- {e}" for e in errors[:40]))
    else:
        parts.append("NO ERRORS in TypeScript, ESLint and the Remotion checks.")
    brief_notes = fidelity(d)
    if brief_notes:
        parts.append("FIDELITY TO THE BRIEF (BRIEF.md vs what is on screen):\n" + "\n".join(f"- {n}" for n in brief_notes))
    if warnings:
        parts.append("WARNINGS (fix them unless you have a precise reason):\n" + "\n".join(f"- {w}" for w in warnings[:20]))
    if others:
        parts.append(f"(There are {others} TypeScript errors in other files of the project, not yours: ignore them, do not touch them.)")
    parts.append("Next step: " + ("fix the errors with edit_file and run check_code again."
                                  if errors else "review_frames on the composition."))
    return "\n\n".join(parts)


# ---------------------------------------------------------------- describe_media

def media_duration(f: Path) -> str:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return "unknown duration"
    try:
        out = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                             capture_output=True, text=True, timeout=20).stdout.strip()
        s = float(out)
        return f"{s:.2f} s = {round(s * 30)} frames at 30 fps"
    except Exception:
        return "unknown duration"


@mcp.tool()
def describe_media(path: str) -> str:
    """List the images, audio and video in a folder with size, duration and content.

    path: a folder inside public/ (e.g. "trip") or a folder in the user's home
    (e.g. "/home/you/Pictures/trip"): in that case the files are copied into
    public/<folder name>/ and the returned paths are already the ones to use.
    For each photo it returns a PhotoInfo line ready for the kit's <Photo>, with the
    focus point (where the subject is). ALWAYS use it before using photos: you cannot see them.
    """
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = PUBLIC / path.strip("/").removeprefix("public/")
    p = p.resolve()
    if not p.is_dir():
        return f"Folder not found: {p}"
    if Path.home().resolve() not in p.parents:
        return "I can only read folders inside the user's home."
    copied = False
    if PUBLIC.resolve() not in [p, *p.parents]:
        dest = PUBLIC / p.name
        dest.mkdir(parents=True, exist_ok=True)
        for f in p.iterdir():
            if f.is_file() and f.suffix.lower() in IMAGES | AUDIO | VIDEO:
                shutil.copy2(f, dest / f.name)
        p, copied = dest, True
    lines = [f"Copied into {p.relative_to(PROJECT)}/." if copied else f"Folder {p.relative_to(PROJECT)}/."]
    photos = []
    for f in sorted(p.iterdir()):
        rel = f.relative_to(PUBLIC).as_posix()
        ext = f.suffix.lower()
        if ext in IMAGES:
            with Pil.open(f) as img:
                w, h = ImageOps.exif_transpose(img).size
            photos.append((f, rel, w, h))
        elif ext in AUDIO:
            lines.append(f"AUDIO {rel}: {media_duration(f)}. Usage: <Audio src={{staticFile(\"{rel}\")}} />")
        elif ext in VIDEO:
            lines.append(f"VIDEO {rel}: {media_duration(f)}. Usage: <OffthreadVideo src={{staticFile(\"{rel}\")}} />")
    for f, rel, w, h in photos:
        shape = "landscape" if w > h * 1.1 else "portrait" if h > w * 1.1 else "square"
        desc = ask_vision([("", f)], (
            "Look at this photo. Never name or identify any person, even if they look famous: describe only "
            "what is visible. Reply with exactly three lines:\n"
            "SUBJECT: who or what is shown, pose, mood, dominant colors (max 25 words).\n"
            "FOCUS: x,y — the center of the main subject's face (or of the main subject if there is "
            "no face), as integer percentages of image width and height from the top-left corner.\n"
            "NOTES: quality problems (low resolution, blur, watermark, text, borders) or 'none'."
        ), side=1024, max_tokens=4000, effort="none")
        m = re.search(r"FOCUS:\s*(\d{1,3})\s*[,;]\s*(\d{1,3})", desc)
        fx, fy = (int(m.group(1)), int(m.group(2))) if m else (50, 35)
        fx, fy = min(max(fx, 0), 100), min(max(fy, 0), 100)
        full = max(1080 / w, 1920 / h)  # enlargement to fill a vertical 1080x1920 frame
        max_crop = max(1.0, round(2.2 / full, 2))
        small = (f" Full-screen 9:16 it is enlarged {full:.1f}x"
                 + (" (soft: prefer a smaller box, e.g. layout B, or a dark texture)." if full > 2 else ".")
                 + f" Keep crop <= {max_crop} or it turns to mush.")
        lines.append(
            f"PHOTO {rel}: {w}x{h}, {shape}.{small}\n"
            f"  {desc.replace(chr(10), chr(10) + '  ')}\n"
            f"  PhotoInfo: {{ src: \"{rel}\", w: {w}, h: {h}, focus: [{fx}, {fy}] }}"
            + ("" if m else "  (focus guessed: vision unavailable)")
        )
    if len(lines) == 1:
        lines.append("No images, audio or video in the folder.")
    lines.append("Use only these files and this data. Do not invent what the photos show.")
    return "\n".join(lines)


# ---------------------------------------------------------------- review_frames

def render_stills(composition: str, frames: list[int], scale: float = SCALE) -> dict:
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    out_dir = CHECK_DIR if scale == SCALE else CHECK_DIR / "pacing"
    cmd = ["node", str(BASE / "stills.mjs"), str(PROJECT), composition, str(out_dir), str(scale),
           *map(str, frames)]
    code, out = run(cmd, timeout=600)
    if "@@ERROR@@" in out:
        err = json.loads(out.split("@@ERROR@@", 1)[1].strip().splitlines()[0])["error"]
        raise RuntimeError(f"The composition crashes while loading (before any frame is drawn):\n{err}\n"
                           "Fix this exact error in the file and line shown. Other compositions are not involved.")
    if "@@RESULT@@" not in out:
        tail = "\n".join(out.strip().splitlines()[-25:])
        raise RuntimeError(f"Rendering the frames failed (exit code {code}):\n{tail}")
    return json.loads(out.split("@@RESULT@@", 1)[1].strip().splitlines()[0])


def empty_band(img: Pil.Image, height: int) -> tuple[float, int, int]:
    """Longest run of flat rows inside the safe area (y 220..height-400, video px).
    Returns (share of the safe area, start y, end y). Flat = nothing drawn there."""
    small = img.convert("L").resize((135, 240))
    k = 240 / height
    top, bottom = round(220 * k), round((height - 400) * k)
    best = cur = start = best_start = 0
    for y in range(top, bottom):
        if ImageStat.Stat(small.crop((0, y, 135, y + 1))).stddev[0] < 4:
            if cur == 0:
                start = y
            cur += 1
            if cur > best:
                best, best_start = cur, start
        else:
            cur = 0
    return best / (bottom - top), round(best_start / k), round((best_start + best) / k)


def scene_timeline(composition: str) -> list[tuple[str, int, int]]:
    """(scene, start, length) parsed from makeTimeline([{ len, Comp }]) in src/<composition>/index.tsx."""
    index = SRC / composition / "index.tsx"
    if not index.exists():
        return []
    out, start = [], 0
    for m in re.finditer(r"\{\s*len:\s*(\d+)\s*,\s*Comp:\s*(\w+)\s*\}", index.read_text(errors="replace")):
        out.append((m.group(2), start, int(m.group(1))))
        start += int(m.group(1))
    return out


def scene_at(timeline: list[tuple[str, int, int]], frame: int) -> str:
    for name, start, length in timeline:
        if start <= frame < start + length:
            return f"scene {name}, local frame {frame - start} of {length}"
    return "unknown scene"


def pacing_thumb(img: Pil.Image) -> Pil.Image:
    return img.convert("L").resize((270, 480), Pil.BOX).filter(ImageFilter.GaussianBlur(1.2))


def pacing(composition: str, timeline: list[tuple[str, int, int]], fps: int) -> list[str]:
    """Per scene, find stretches where (almost) nothing moves. The last 15 frames are skipped:
    there the scene transition moves anyway."""
    plan, frames = [], set()
    for name, start, length in timeline:
        local = sorted({x for x in (0, 12, 30, 60, 100, 150, 200, length - 46, length - 16) if 0 <= x < length - 15})
        plan.append((name, start, length, local))
        frames |= {start + x for x in local}
    if not frames:
        return []
    res = render_stills(composition, sorted(frames), scale=0.25)
    shots = {s["frame"]: pacing_thumb(Pil.open(s["path"])) for s in res["stills"]}
    notes = []
    for name, start, length, local in plan:
        spans = []  # (a, b, change per frame)
        for a, b in zip(local, local[1:]):
            if b - a >= 4 and start + a in shots and start + b in shots:
                spans.append((a, b, ImageStat.Stat(ImageChops.difference(shots[start + a], shots[start + b])).mean[0] / (b - a)))
        for limit, frames_max, label, advice in (
            (0.025, 75, "FROZEN", "nothing moves"),
            (0.07, 105, "SLOW", "only a slow drift moves"),
        ):
            run_start = run_end = None
            best = (0, 0, 0)
            for a, b, d in spans:
                if d < limit:
                    run_start = a if run_start is None else run_start
                    run_end = b
                    if run_end - run_start > best[0]:
                        best = (run_end - run_start, run_start, run_end)
                else:
                    run_start = None
            if best[0] > frames_max:
                notes.append(f"- {name}: {label} for {best[0] / fps:.1f} s (local frames {best[1]}-{best[2]}): {advice}. "
                             f"Shorten the scene (about {best[0] - 40} frames less) or add a new beat there.")
                break
    return notes


def thumb(img: Pil.Image) -> Pil.Image:
    """Small blurred grayscale copy: film grain averages out, real motion stays."""
    return img.convert("L").resize((135, 240), Pil.BOX).filter(ImageFilter.GaussianBlur(1))


def with_guides(img: Pil.Image, height: int) -> Pil.Image:
    """Copy of a vertical frame with the safe area drawn on it, so the reviewer judges positions
    against visible lines instead of guessing pixels (y=220 and y=height-400 in video pixels)."""
    out = img.convert("RGB").copy()
    draw = ImageDraw.Draw(out)
    k = out.height / height
    for y in (220 * k, (height - 400) * k):
        for x in range(0, out.width, 16):
            draw.line([(x, y), (x + 8, y)], fill=(255, 40, 40), width=2)
    draw.text((6, 220 * k - 14), "UI ZONE ABOVE", fill=(255, 40, 40))
    draw.text((6, (height - 400) * k + 4), "UI ZONE BELOW", fill=(255, 40, 40))
    return out


def contact_sheet(images: list[tuple[int, Pil.Image]], fps: int, dest: Path) -> None:
    """Contact sheet for the user: the frames in a grid with their timecode."""
    w, h = 270, round(270 * images[0][1].height / images[0][1].width)
    cols = min(4, len(images))
    rows = -(-len(images) // cols)
    sheet = Pil.new("RGB", (cols * (w + 12) + 12, rows * (h + 44) + 12), "#111")
    draw = ImageDraw.Draw(sheet)
    for i, (f, img) in enumerate(images):
        x, y = 12 + (i % cols) * (w + 12), 12 + (i // cols) * (h + 44)
        sheet.paste(img.convert("RGB").resize((w, h)), (x, y))
        draw.text((x, y + h + 8), f"f{f}  {f / fps:.1f}s", fill="#ddd")
    sheet.save(dest, quality=90)


@mcp.tool()
def review_frames(composition: str, frames: list[int] | None = None, brief: str = "") -> str:
    """Render some frames of the composition and have an art director judge them.

    composition: the <Composition> id, for example "LaunchTrailer".
    frames: optional. If omitted, 8 frames spread over the whole video are picked.
            Pass them to re-check a specific scene after a fix.
    brief: optional. One sentence on what the video must convey, for a better review.
    Returns, per frame, the visible problems (cut, overlapping or unreadable text,
    distorted photos, empty or frozen scenes) and the most important fixes.
    Use it after check_code reports no errors.
    """
    n = _reviews.get(composition, 0) + 1
    _reviews[composition] = n
    if n > MAX_REVIEWS:
        return (f"BLOCKED: you already reviewed {composition} {MAX_REVIEWS} times. Do not call this tool "
                "again. Render the video with render_video and honestly report the remaining problems to the user.")
    t0 = time.monotonic()
    try:
        meta = render_stills(composition, [])["meta"]
    except RuntimeError as e:
        return f"{e}\n\nCheck the composition id and run check_code."
    duration, fps = meta["durationInFrames"], meta["fps"]
    if frames:
        picked = sorted({min(max(int(f), 0), duration - 1) for f in frames})[:12]
    else:
        picked = sorted({min(duration - 1, round((i + 0.5) * duration / AUTO_FRAMES)) for i in range(AUTO_FRAMES)})
    pairs = sorted({f for p in picked for f in (p, min(p + MOTION_GAP, duration - 1))})
    try:
        res = render_stills(composition, pairs)
    except RuntimeError as e:
        return str(e)
    paths = {s["frame"]: Path(s["path"]) for s in res["stills"]}
    timeline = scene_timeline(composition)
    lines = [f"{composition}: {meta['width']}x{meta['height']}, {fps} fps, {duration} frames "
             f"({duration / fps:.1f} s). Review {n} of {MAX_REVIEWS}."]
    for e in res["errors"]:
        lines.append(f"RENDER ERROR at frame {e['frame']} ({scene_at(timeline, e['frame'])}):\n{e['error']}")
    images, frozen = [], 0
    for f in picked:
        if f not in paths:
            continue
        img = Pil.open(paths[f]).convert("RGB")
        images.append((f, img))
        notes = []
        if ImageStat.Stat(img.convert("L")).stddev[0] < 6:
            notes.append("NEARLY EMPTY: flat color, nothing visible")
        if meta["height"] > meta["width"]:
            share, y0, y1 = empty_band(img, meta["height"])
            if share > 0.3:
                notes.append(f"EMPTY BAND y={y0}-{y1} ({share:.0%} of the safe area): fill it (bigger text, move the "
                             "text block into it, or a taller photo box) unless it is a deliberate typographic pause")
        g = min(f + MOTION_GAP, duration - 1)
        if g in paths and g != f:
            diff = ImageStat.Stat(ImageChops.difference(thumb(img), thumb(Pil.open(paths[g])))).mean[0]
            if diff < 0.1:
                notes.append(f"FROZEN: nothing changes between frame {f} and {g} (1 s)")
                frozen += 1
        lines.append(f"- f{f} ({f / fps:.1f} s): " + ("; ".join(notes) if notes else "passes the automatic checks"))
    if frozen > len(images) / 2:
        lines.append("MANY FROZEN SCENES: in a professional video something always moves (slow zoom on photos, "
                     "text entering, backgrounds drifting).")
    if timeline and not frames:
        try:
            pace = pacing(composition, timeline, fps)
        except RuntimeError:
            pace = []
        lines.append("\nPACING (measured on the pixels, per scene):\n" + ("\n".join(pace) if pace else
                     "- no frozen or slow stretches: good rhythm."))
    if images:
        sheet = CHECK_DIR / f"{composition}-contact-sheet.jpg"
        contact_sheet(images, fps, sheet)
        vertical = meta["height"] > meta["width"]
        kind = "vertical 9:16 social reel" if vertical else f"{meta['width']}x{meta['height']} video"
        shown = [(f, with_guides(img, meta["height"]) if vertical else img) for f, img in images]
        verdict = ask_vision(
            [(f"Frame {f} ({f / fps:.1f} s):", img) for f, img in shown],
            f"These are {len(images)} frames, in time order, of a {kind} made with Remotion"
            + (f". Brief: {brief}" if brief else "") + ".\n"
            "You are a demanding art director. Check every frame for CONCRETE defects only:\n"
            "- text cut off by the frame edge, overflowing, or wrapping badly (one word alone on a line)\n"
            "- text touching or nearly touching the left/right edge, or clearly off-center when it should be centered\n"
            "- elements overlapping each other or covering faces\n"
            "- text with poor contrast over a busy image; text too small to read on a phone\n"
            + ("- text beyond the red dashed lines (covered by the app interface). The red lines are guides added "
               "for you, not part of the video. Text between the two lines is SAFE: never ask to move it\n"
               if vertical else "")
            + "- empty or near-empty frames, large dead areas (an empty band over a quarter of the frame), hard edges "
            "where a photo box ends abruptly, photos squashed, stretched, pixelated, "
            "or cropped so the face is cut\n"
            "- spelling mistakes in the visible text\n"
            "Elements that are semi-transparent because they are animating in are expected: do not flag them.\n"
            "Then judge the whole: does it look like professional motion design or like an amateur "
            "template (system fonts, everything centered, same layout repeated, timid sizes, clichés)? "
            "Is there a clear visual hierarchy, a consistent palette and type system, variety between scenes?\n"
            "Be blunt, no praise. Reply in this exact format:\n"
            "F<frame>: OK, or the defects found\n...\n"
            "SCORE: <1-10>/10\n"
            "FIXES: the 3 most important fixes, each concrete (which element, where, what to change, by how much)."
        )
        lines.append("\nVISUAL REVIEW (what is actually visible in the frames):\n" + verdict)
        lines.append(f"\nContact sheet for the user: {sheet.relative_to(PROJECT)}")
    lines.append(f"(review took {time.monotonic() - t0:.0f} s)")
    lines.append(
        "\nNEXT STEP: fix the reported problems, starting with anything that makes text unreadable or cut. "
        "Then check_code, and review_frames again only on the frames of the scenes you fixed. "
        "If the score is at least 8 and no defects are left, go to render_video."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------- render_video

def notify_telegram(video: Path, caption: str) -> str:
    """Send the video to the user's Telegram bot, if one is configured (telegram_bot/setup_bot.py).
    Runs in the background so the tool returns at once. QWEN_TELEGRAM_NOTIFY=0 turns it off."""
    if os.environ.get("QWEN_TELEGRAM_NOTIFY", "1") == "0":
        return ""
    import sys
    import threading
    sys.path.insert(0, str(BASE.parent / "telegram_bot"))
    try:
        from telegram_api import Bot, configured
    except ImportError:
        return ""
    if not configured():
        return ""
    threading.Thread(target=lambda: Bot.from_config().send_video(video, caption), daemon=True).start()
    return " It is also being sent to the user's Telegram."


@mcp.tool()
def render_video(composition: str) -> str:
    """Render the final video to out/<composition>.mp4 and open it for the user.

    composition: the <Composition> id. Use it only after check_code reports no errors
    and at least one review_frames. It can take a few minutes.
    """
    out = PROJECT / "out" / f"{composition}.mp4"
    t0 = time.monotonic()
    code, text = run(["npx", "--no-install", "remotion", "render", composition, str(out)], timeout=1500)
    if code != 0 or not out.exists():
        tail = "\n".join(line for line in text.strip().splitlines()[-30:] if line.strip())
        return f"RENDER FAILED (exit code {code}):\n{tail}\n\nFix the error, run check_code and try again."
    _reviews.pop(composition, None)
    if OPEN_VIDEO and shutil.which("xdg-open"):
        subprocess.Popen(["xdg-open", str(out)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    mb = out.stat().st_size / 1e6
    telegram = notify_telegram(out, f"{composition} · {mb:.1f} MB · rendered in {time.monotonic() - t0:.0f} s")
    return (f"Video ready: {out} ({mb:.1f} MB, rendered in {time.monotonic() - t0:.0f} s). It has opened on the "
            f"user's screen.{telegram}\n\nNOW STOP and answer the user: where the file is, what the video looks like scene "
            "by scene, and the problems that remain according to the last visual review. Do not call it perfect "
            "if the review reported defects.")


if __name__ == "__main__":
    mcp.run()
