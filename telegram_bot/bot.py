"""Telegram bot: start a video on this PC from anywhere, and get every result back.

Commands (only the owner's chat is obeyed; everyone else is ignored). A text file dropped in
jobs/inbox/ is treated like /video, to start videos from the PC itself.
    /video <brief>   start a video (queued if one is running). Attach photos, audio or video
                     files with /video as the caption: they become the material for the video.
    /status          what's running, progress, last review score, GPU temperature
    /cancel          stop the running video
    /last            send the last finished video again
    /model [id]      show or change the model used for new videos
    /help

Each job: keeps the PC awake, loads the model in LM Studio, runs the same agent loop Bionic
uses (eval/run_agent.py: skill + remotion-check tools), reports review scores as they come,
and sends the final video, the contact sheet and the agent's report to Telegram.
"""
import json
import os
import queue
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from telegram_api import Bot, load_config, save_config

ROOT = Path(__file__).resolve().parent.parent
AGENT = ROOT / "agent" / "run_agent.py"
PYTHON = ROOT / "remotion-check" / ".venv" / "bin" / "python"
JOBS = ROOT / "jobs"
REMOTION = Path(os.environ.get("REMOTION_PROJECT", ROOT / "remotion-template")).expanduser().resolve()
LMS = Path(os.environ.get("LMS_BIN", Path.home() / ".lmstudio" / "bin" / "lms"))
LMSTUDIO = os.environ.get("LMSTUDIO_URL", "http://127.0.0.1:1234")
DEFAULT_MODEL = os.environ.get("VIDEO_MODEL", "qwen/qwen3.8-27b")
CONTEXT = 73728      # 27B Q4 + vision adapter on 24 GB, with 8-bit KV cache and no MTP draft
                     # (see the model's load config in LM Studio: kCacheQuantizationType q8_0)
MAX_STEPS = 120
COOL_DOWN_S = 600    # pause between queued videos, for the GPU
MEDIA_EXT = {".jpg", ".jpeg", ".png", ".webp", ".mp3", ".wav", ".m4a", ".ogg", ".mp4", ".mov", ".webm"}


@dataclass
class Job:
    id: str
    brief: str
    model: str
    files: list[Path] = field(default_factory=list)
    proc: subprocess.Popen | None = None
    started: float = 0.0
    cancelled: bool = False

    @property
    def dir(self) -> Path:
        return JOBS / self.id


class VideoBot:
    def __init__(self) -> None:
        self.bot = Bot.from_config()
        self.owner = self.bot.chat_id
        self.jobs: queue.Queue[Job] = queue.Queue()
        self.current: Job | None = None
        self.albums: dict[str, dict] = {}  # media_group_id -> {"files", "caption", "t"}
        self.last_video: Path | None = None

    # ------------------------------------------------------------ helpers
    @property
    def model(self) -> str:
        return load_config().get("model", DEFAULT_MODEL)

    def gpu(self) -> str:
        try:
            out = subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu,power.draw,power.limit",
                                  "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10).stdout
            temp, draw, limit = [x.strip() for x in out.split(",")]
            return f"GPU {temp} °C, {float(draw):.0f} W of {float(limit):.0f} W limit"
        except Exception:
            return "GPU status unavailable"

    def agent_running(self) -> bool:
        """True if an agent started outside this bot (e.g. a test run) is using the GPU."""
        return self.external_log() is not None

    def vision_models(self) -> list[str]:
        models = httpx.get(f"{LMSTUDIO}/api/v0/models", timeout=10).json()["data"]
        return [m["id"] for m in models if m.get("type") == "vlm"]

    def ensure_server(self) -> None:
        """Start LM Studio headless (daemon + API server) if nothing answers, e.g. after a reboot."""
        try:
            httpx.get(f"{LMSTUDIO}/api/v0/models", timeout=5)
            return
        except httpx.HTTPError:
            pass
        subprocess.run([str(LMS), "daemon", "up"], capture_output=True, timeout=120)
        subprocess.run([str(LMS), "server", "start"], capture_output=True, timeout=120)
        for _ in range(30):
            try:
                httpx.get(f"{LMSTUDIO}/api/v0/models", timeout=5)
                return
            except httpx.HTTPError:
                time.sleep(2)
        raise RuntimeError("LM Studio is not running and could not be started (lms daemon up / lms server start).")

    def ensure_model(self, model: str) -> None:
        self.ensure_server()
        models = {m["id"]: m for m in httpx.get(f"{LMSTUDIO}/api/v0/models", timeout=10).json()["data"]}
        if models.get(model, {}).get("state") == "loaded":
            return
        subprocess.run([str(LMS), "unload", "--all"], capture_output=True, timeout=120)
        for ctx in (CONTEXT, 49152):  # fall back to 48k if other apps hold VRAM
            r = subprocess.run([str(LMS), "load", model, "-c", str(ctx), "--parallel", "1", "--gpu", "max",
                                "--no-speculative-draft-mtp", "-y"], capture_output=True, text=True, timeout=600)
            if "success" in (r.stdout + r.stderr).lower():
                return
            subprocess.run([str(LMS), "unload", "--all"], capture_output=True, timeout=120)
        raise RuntimeError(f"could not load {model}: {(r.stdout + r.stderr)[-300:]}")

    # ------------------------------------------------------------ incoming messages
    def handle(self, msg: dict) -> None:
        if msg["chat"]["id"] != self.owner:
            return  # not the owner: ignore silently
        text = (msg.get("text") or msg.get("caption") or "").strip()
        has_media = any(k in msg for k in ("photo", "document", "audio", "video"))
        if has_media and msg.get("media_group_id"):
            album = self.albums.setdefault(msg["media_group_id"], {"msgs": [], "caption": "", "t": 0.0})
            album["msgs"].append(msg)
            album["caption"] = album["caption"] or text
            album["t"] = time.monotonic()
            return
        if has_media:
            if text.startswith("/video"):
                self.new_job(text, [msg])
            else:
                self.bot.send("To use these files in a video, send them with a caption starting with /video.")
            return
        cmd, _, arg = text.partition(" ")
        cmd = cmd.split("@")[0].lower()
        if cmd in ("/start", "/help"):
            self.bot.send(__doc__.split("Each job:")[0].strip())
        elif cmd == "/video":
            self.new_job(text, [])
        elif cmd == "/status":
            self.bot.send(self.status())
        elif cmd == "/cancel":
            self.cancel()
        elif cmd == "/last":
            self.bot.send(self.bot.send_video(self.last_video, "Last video") if self.last_video
                          else "No finished video yet.")
        elif cmd == "/model":
            self.set_model(arg.strip())
        else:
            self.bot.send("Unknown command. Send /help.")

    def check_inbox(self) -> None:
        """Local submissions: a text file in jobs/inbox/ is treated like /video <its text>."""
        inbox = JOBS / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        for f in sorted(inbox.glob("*.txt")):
            brief = f.read_text(errors="replace").strip()
            f.rename(f.with_suffix(".queued"))
            if brief:
                self.new_job("/video " + brief, [])

    def flush_albums(self) -> None:
        for gid, album in list(self.albums.items()):
            if time.monotonic() - album["t"] > 4:  # all parts of an album arrive within a few seconds
                del self.albums[gid]
                if album["caption"].startswith("/video"):
                    self.new_job(album["caption"], album["msgs"])
                else:
                    self.bot.send("To use these files in a video, send them with a caption starting with /video.")

    def new_job(self, text: str, media_msgs: list[dict]) -> None:
        brief = text.partition(" ")[2].strip()
        if not brief:
            self.bot.send("Write the brief after the command, e.g.\n/video A 30-second vertical reel about ...")
            return
        job = Job(id=time.strftime("%Y%m%d-%H%M%S"), brief=brief, model=self.model)
        folder = REMOTION / "public" / f"tg-{job.id}"
        for m in media_msgs:
            item = m["photo"][-1] if "photo" in m else m.get("document") or m.get("audio") or m.get("video")
            name = item.get("file_name") or f"photo-{len(job.files) + 1}.jpg"
            if Path(name).suffix.lower() in MEDIA_EXT:
                job.files.append(self.bot.download(item["file_id"], folder / name))
        if job.files:
            job.brief += f"\n\nMaterial for this video (sent from Telegram): {folder}"
        self.jobs.put(job)
        position = self.jobs.qsize() + (1 if self.current else 0)
        files = f", {len(job.files)} file(s) attached" if job.files else ""
        self.bot.send(f"Video #{job.id} {'queued (position ' + str(position) + ')' if self.current else 'starting'}"
                      f"{files}. Model: {job.model}. Expect 30-90 minutes; I'll send progress and the result here.")

    def external_run(self) -> str | None:
        """Describe an agent run started outside the bot (e.g. a test), read from its --log file."""
        log = self.external_log()
        if not log:
            return None
        steps, scores, ctx, secs = 0, [], 0, 0
        if log.exists():
            for line in log.read_text(errors="replace").splitlines():
                row = json.loads(line)
                if "message" in row:
                    steps, ctx, secs = row["step"], row.get("usage", {}).get("prompt_tokens", 0), row.get("t", 0)
                elif row.get("tool") == "review_frames":
                    s = re.search(r"SCORE:\s*(\d+)/10", row.get("result", ""))
                    scores.append(f"{s.group(1)}/10" if s else "n/a")
        age = secs / 60
        return (f"A video started outside the bot is running ({log.stem}): ~{age:.0f} min, step {steps}, "
                f"context {ctx // 1000}k/{CONTEXT // 1000}k, reviews: {', '.join(scores) if scores else 'none yet'}.")

    def agent_processes(self) -> list[tuple[int, list[str]]]:
        """(pid, argv) of python processes really running run_agent.py (not shells that mention it)."""
        pids = subprocess.run(["pgrep", "-f", "run_agent.py"], capture_output=True, text=True).stdout.split()
        found = []
        for pid in pids:
            try:
                argv = Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="replace").split("\0")
            except OSError:
                continue
            if "python" in Path(argv[0]).name and any(a.endswith("run_agent.py") for a in argv[1:3]):
                found.append((int(pid), argv))
        return found

    def external_log(self) -> Path | None:
        for pid, argv in self.agent_processes():
            if "--log" not in argv:
                continue
            log = Path(argv[argv.index("--log") + 1])
            log = log if log.is_absolute() else Path(f"/proc/{pid}/cwd").resolve() / log
            if self.current and log.parent == self.current.dir:
                continue  # the bot's own job
            return log
        return None

    def watch_external(self) -> None:
        """When a run started outside the bot ends, send its result too: success or failure."""
        log = self.external_log()
        if log:
            self.watched = log
            return
        if not getattr(self, "watched", None):
            return
        log, self.watched = self.watched, None
        rows = [json.loads(line) for line in log.read_text(errors="replace").splitlines()] if log.exists() else []
        videos = [m.group(1) for r in rows if r.get("tool") == "render_video"
                  for m in [re.search(r"Video ready: (\S+\.mp4)", r.get("result", ""))] if m]
        final = next((r["message"].get("content") or "" for r in reversed(rows)
                      if "message" in r and not r["message"].get("tool_calls")), "")
        scores = [s.group(1) + "/10" for r in rows if r.get("tool") == "review_frames"
                  for s in [re.search(r"SCORE:\s*(\d+)/10", r.get("result", ""))] if s]
        steps = max((r["step"] for r in rows if "message" in r), default=0)
        caption = f"{log.stem}: finished after {steps} steps" + (f", reviews {', '.join(scores)}" if scores else "")
        if videos and Path(videos[-1]).exists():
            self.last_video = Path(videos[-1])
            self.bot.send_video(self.last_video, caption)
        else:
            self.bot.send(f"{caption}. No video was rendered.")
        if final.strip():
            self.bot.send("Agent's report:\n" + final.strip()[:3500])

    def status(self) -> str:
        if not self.current:
            external = self.external_run()
            if external:
                return f"{external} {self.jobs.qsize()} bot job(s) queued. {self.gpu()}."
            return f"Idle. {self.jobs.qsize()} queued. {self.gpu()}."
        job = self.current
        mins = (time.monotonic() - job.started) / 60
        out = job.dir / "run.out"
        steps = re.findall(r"^\[(\d+)\] \d+s ctx=(\d+)", out.read_text(errors="replace"), re.M) if out.exists() else []
        step = f"step {steps[-1][0]}/{MAX_STEPS}, context {int(steps[-1][1]) // 1000}k/{CONTEXT // 1000}k" if steps else "starting"
        scores = self.scores(job)
        return (f"Video #{job.id}: {mins:.0f} min, {step}. "
                f"Reviews: {', '.join(scores) if scores else 'none yet'}. "
                f"{self.jobs.qsize()} queued. {self.gpu()}.\nBrief: {job.brief[:300]}")

    def cancel(self) -> None:
        job = self.current
        if not job or not job.proc:
            self.bot.send("Nothing is running.")
            return
        job.cancelled = True
        job.proc.terminate()
        self.bot.send(f"Stopping video #{job.id}...")

    def set_model(self, model: str) -> None:
        try:
            available = self.vision_models()
        except Exception as e:
            self.bot.send(f"LM Studio not reachable: {e}")
            return
        if not model:
            self.bot.send(f"Model for new videos: {self.model}\nAvailable (with vision): " + ", ".join(available))
        elif model in available:
            cfg = load_config()
            cfg["model"] = model
            save_config(cfg)
            self.bot.send(f"New videos will use {model}.")
        else:
            self.bot.send(f"Unknown or non-vision model. Available: {', '.join(available)}")

    # ------------------------------------------------------------ job runner
    def scores(self, job: Job) -> list[str]:
        log = job.dir / "run.jsonl"
        if not log.exists():
            return []
        out = []
        for line in log.read_text(errors="replace").splitlines():
            row = json.loads(line)
            if row.get("tool") == "review_frames":
                m = re.search(r"SCORE:\s*(\d+)/10", row.get("result", ""))
                out.append(f"{m.group(1)}/10" if m else "n/a")
        return out

    def run(self, job: Job) -> None:
        job.dir.mkdir(parents=True, exist_ok=True)
        (job.dir / "brief.txt").write_text(job.brief)
        awake = subprocess.Popen(["systemd-inhibit", "--what=sleep:idle", "--who=qwen-video-bot",
                                  f"--why=Rendering video {job.id}", "sleep", "infinity"])
        try:
            if "350" in self.gpu():
                self.bot.send("Note: the GPU power limit is back at 350 W (it resets on reboot). "
                              "It will run hotter: `sudo nvidia-smi -pl 260` lowers it.")
            if self.agent_running():
                self.bot.send(f"Another video is already being made on this PC: #{job.id} will start when it ends.")
                while self.agent_running():
                    time.sleep(60)
            self.ensure_model(job.model)
            job.started = time.monotonic()
            self.bot.send(f"Video #{job.id} started with {job.model}.")
            with (job.dir / "run.out").open("w") as out:
                job.proc = subprocess.Popen(
                    [str(PYTHON), "-u", str(AGENT), job.brief, "--model", job.model,
                     "--max-steps", str(MAX_STEPS), "--log", str(job.dir / "run.jsonl"),
                     *(["--effort", load_config()["effort"]] if load_config().get("effort") else [])],
                    cwd=AGENT.parent, stdout=out, stderr=subprocess.STDOUT,
                    env={**os.environ, "QWEN_TELEGRAM_NOTIFY": "0"})
                reported = 0
                while job.proc.poll() is None:
                    time.sleep(20)
                    scores = self.scores(job)
                    for s in scores[reported:]:
                        reported += 1
                        self.bot.send(f"Video #{job.id}: review {reported} → {s}")
            self.report(job)
        except Exception as e:
            self.bot.send(f"Video #{job.id} failed: {e}")
        finally:
            awake.terminate()

    def report(self, job: Job) -> None:
        text = (job.dir / "run.out").read_text(errors="replace")
        mins = (time.monotonic() - job.started) / 60
        if job.cancelled:
            self.bot.send(f"Video #{job.id} cancelled after {mins:.0f} min.")
            return
        videos = re.findall(r"Video ready: (\S+\.mp4)", text)
        final = text.split("FINAL ANSWER", 1)[1].split(":", 1)[1].strip() if "FINAL ANSWER" in text else ""
        scores = self.scores(job)
        caption = (f"Video #{job.id} · {job.model} · {mins:.0f} min"
                   + (f" · reviews {', '.join(scores)}" if scores else ""))
        if not videos:
            fallback = self.fallback_render(job)
            if fallback:
                videos = [str(fallback)]
                caption += " · auto-render: the agent stopped before rendering"
        if videos and Path(videos[-1]).exists():
            video = Path(videos[-1])
            self.last_video = video
            result = self.bot.send_video(video, caption)
            if not result.startswith("Sent"):
                self.bot.send(result)
            sheet = REMOTION / "out" / "check" / f"{video.stem}-contact-sheet.jpg"
            if sheet.exists():
                self.bot.send_photo(sheet, "Frames from the last review")
        else:
            self.bot.send(f"{caption}\nNo video was rendered.")
        if final:
            self.bot.send("Agent's report:\n" + final[:3500])

    def fallback_render(self, job: Job) -> Path | None:
        """If the agent wrote a composition but never rendered it, render it if its code is clean."""
        started = time.time() - (time.monotonic() - job.started)
        folders = [d for d in (REMOTION / "src").iterdir()
                   if (d / "index.tsx").exists() and (d / "index.tsx").stat().st_mtime > started]
        for folder in sorted(folders, key=lambda d: d.stat().st_mtime, reverse=True):
            m = re.search(r'<Composition[^>]*\bid="([^"]+)"', (folder / "index.tsx").read_text(errors="replace"))
            if not m:
                continue
            code = (f"import server; server.OPEN_VIDEO=False; r=server.check_code({folder.name!r});"
                    f"print(r if r.startswith('ERRORS') else server.render_video({m.group(1)!r}))")
            out = subprocess.run([str(PYTHON), "-c", code], cwd=ROOT / "remotion-check", capture_output=True,
                                 text=True, timeout=1800, env={**os.environ, "QWEN_TELEGRAM_NOTIFY": "0"}).stdout
            found = re.search(r"Video ready: (\S+\.mp4)", out)
            if found:
                return Path(found.group(1))
            self.bot.send(f"Auto-render of {folder.name} not possible:\n{out[:800]}")
        return None

    def worker(self) -> None:
        while True:
            job = self.jobs.get()
            self.current = job
            self.run(job)
            self.current = None
            if not self.jobs.empty():
                self.bot.send(f"Cooling the GPU down for {COOL_DOWN_S // 60} minutes before the next video.")
                time.sleep(COOL_DOWN_S)

    def serve(self) -> None:
        threading.Thread(target=self.worker, daemon=True).start()
        try:
            self.bot.send(f"localmotion bot is online. {self.gpu()}. Send /video <brief> to start.")
        except Exception:
            pass  # no network yet: the polling loop below retries
        offset = None
        while True:
            try:
                for u in self.bot.updates(offset=offset, timeout=30):
                    offset = u["update_id"] + 1
                    if "message" in u:
                        try:
                            self.handle(u["message"])
                        except Exception as e:
                            self.bot.send(f"Error: {e}")
                self.flush_albums()
                self.watch_external()
                self.check_inbox()
            except Exception as e:
                print(f"polling error: {e!r}", flush=True)  # visible in journalctl
                time.sleep(10)  # network hiccup: retry


if __name__ == "__main__":
    VideoBot().serve()
