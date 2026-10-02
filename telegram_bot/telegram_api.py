"""Minimal Telegram Bot API client shared by the setup wizard, the bot and the MCP server.

Configuration lives in ~/.config/qwen-video-bot/config.json (written by setup_bot.py):
    {"token_file": "/path/to/token", "chat_id": 123456789}
The token file holds the bot token and must be readable only by its owner (chmod 600).
"""
import json
import os
import re
from pathlib import Path

import httpx

CONFIG_DIR = Path(os.environ.get("QWEN_BOT_CONFIG_DIR", Path.home() / ".config" / "qwen-video-bot"))
CONFIG_FILE = CONFIG_DIR / "config.json"
MAX_UPLOAD = 50 * 1024 * 1024  # Telegram bots can upload files up to 50 MB


def load_config() -> dict:
    return json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.exists() else {}


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.chmod(0o700)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    CONFIG_FILE.chmod(0o600)


def parse_token(text: str) -> str | None:
    m = re.search(r"\d{6,}:[A-Za-z0-9_-]{30,}", text)
    return m.group(0) if m else None


def configured() -> bool:
    cfg = load_config()
    return bool(cfg.get("token_file") and cfg.get("chat_id") and Path(cfg["token_file"]).exists())


class Bot:
    def __init__(self, token: str, chat_id: int | None = None):
        self.api = f"https://api.telegram.org/bot{token}"
        self.file_api = f"https://api.telegram.org/file/bot{token}"
        self.chat_id = chat_id

    @classmethod
    def from_config(cls) -> "Bot":
        cfg = load_config()
        if not cfg:
            raise RuntimeError(f"Telegram is not configured: run setup_bot.py (missing {CONFIG_FILE}).")
        token = parse_token(Path(cfg["token_file"]).read_text())
        if not token:
            raise RuntimeError(f"No bot token found in {cfg['token_file']}.")
        return cls(token, cfg.get("chat_id"))

    def call(self, method: str, http_timeout: float = 30, **params) -> dict:
        r = httpx.post(f"{self.api}/{method}", data=params, timeout=http_timeout)
        data = r.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram {method} failed: {data.get('description')}")
        return data["result"]

    def me(self) -> dict:
        return self.call("getMe")

    def updates(self, offset: int | None = None, timeout: int = 50) -> list[dict]:
        params = {"timeout": timeout, "allowed_updates": json.dumps(["message"])}
        if offset is not None:
            params["offset"] = offset
        return self.call("getUpdates", http_timeout=timeout + 10, **params)

    def send(self, text: str, chat_id: int | None = None) -> None:
        for i in range(0, max(len(text), 1), 4000):  # Telegram limit: 4096 characters per message
            self.call("sendMessage", chat_id=chat_id or self.chat_id, text=text[i:i + 4000])

    def _upload(self, method: str, field: str, path: Path, mime: str, caption: str, **extra) -> str:
        if path.stat().st_size > MAX_UPLOAD:
            return f"{path.name} is {path.stat().st_size / 1e6:.0f} MB: over the 50 MB bot limit, not sent."
        with path.open("rb") as f:
            r = httpx.post(f"{self.api}/{method}", timeout=900,
                           data={"chat_id": self.chat_id, "caption": caption[:1000], **extra},
                           files={field: (path.name, f, mime)})
        data = r.json()
        return f"Sent {path.name} to Telegram." if data.get("ok") else f"Telegram error: {data.get('description')}"

    def send_video(self, path: Path, caption: str = "") -> str:
        return self._upload("sendVideo", "video", path, "video/mp4", caption, supports_streaming="true")

    def send_photo(self, path: Path, caption: str = "") -> str:
        return self._upload("sendPhoto", "photo", path, "image/jpeg", caption)

    def download(self, file_id: str, dest: Path) -> Path:
        info = self.call("getFile", file_id=file_id)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with httpx.stream("GET", f"{self.file_api}/{info['file_path']}", timeout=300) as r:
            with dest.open("wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)
        return dest
