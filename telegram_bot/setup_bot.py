"""Interactive setup: create your own video bot in a few minutes.

    python setup_bot.py                      # guided setup
    python setup_bot.py --token-file PATH    # reuse a token you already saved in a file
    python setup_bot.py --install-service    # also run the bot at login (systemd user service)

Steps: create a bot with @BotFather, paste its token (hidden input), send any message to
your bot, and this script saves the token (chmod 600) and your chat id so that only you
can command the bot.
"""
import argparse
import getpass
import os
import subprocess
import sys
from pathlib import Path

from telegram_api import CONFIG_DIR, Bot, load_config, parse_token, save_config

HERE = Path(__file__).resolve().parent
SERVICE = "qwen-video-bot.service"


def ask_token() -> Path:
    print("1. On Telegram, open @BotFather and send /newbot.")
    print("2. Choose a name and a username ending in 'bot'.")
    print("3. BotFather replies with a token like 123456789:AA... Paste it here (input is hidden).\n")
    token = parse_token(getpass.getpass("Bot token: "))
    if not token:
        sys.exit("That doesn't look like a bot token (expected 123456789:AA...).")
    path = CONFIG_DIR / "token"
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.chmod(0o700)
    path.write_text(token + "\n")
    path.chmod(0o600)
    return path


def wait_for_chat(bot: Bot, username: str) -> int:
    print(f"\nNow open https://t.me/{username} on Telegram and send it any message (e.g. 'hi').")
    print("Waiting for your message...", flush=True)
    for _ in range(60):  # up to ~10 minutes
        for u in bot.updates(timeout=10):
            msg = u.get("message")
            if msg:
                bot.updates(offset=u["update_id"] + 1, timeout=0)  # acknowledge it
                name = msg["chat"].get("first_name", "you")
                print(f"Got it: chat with {name} (id {msg['chat']['id']}).")
                return msg["chat"]["id"]
    sys.exit("No message received. Run the setup again when you're ready.")


def install_service(python: str) -> None:
    env = "".join(f"Environment={k}={os.environ[k]}\n" for k in ("REMOTION_PROJECT", "VIDEO_MODEL", "LMSTUDIO_URL")
                  if os.environ.get(k))
    unit_dir = Path.home() / ".config" / "systemd" / "user"
    unit_dir.mkdir(parents=True, exist_ok=True)
    (unit_dir / SERVICE).write_text(f"""[Unit]
Description=Qwen video bot (Telegram -> local Remotion agent)
After=network-online.target

[Service]
ExecStart={python} {HERE / 'bot.py'}
WorkingDirectory={HERE}
{env}Restart=on-failure
RestartSec=20

[Install]
WantedBy=default.target
""")
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", SERVICE], check=True)
    print(f"Service installed and started: systemctl --user status {SERVICE}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--token-file", help="use a token already saved in this file")
    ap.add_argument("--install-service", action="store_true", help="run the bot at login with systemd")
    args = ap.parse_args()

    if args.token_file:
        token_file = Path(args.token_file).expanduser().resolve()
        token_file.chmod(0o600)
    else:
        token_file = ask_token()
    token = parse_token(token_file.read_text())
    if not token:
        sys.exit(f"No bot token found in {token_file}.")
    bot = Bot(token)
    username = bot.me()["username"]
    print(f"Token OK: @{username}")

    cfg = load_config()
    chat_id = cfg.get("chat_id") if cfg.get("token_file") == str(token_file) else None
    chat_id = chat_id or wait_for_chat(bot, username)
    save_config({"token_file": str(token_file), "chat_id": chat_id})
    bot.chat_id = chat_id
    bot.send("Your video bot is ready. Send /help to see what I can do.")
    print(f"Saved {CONFIG_DIR / 'config.json'}. A test message was sent to you.")
    if args.install_service:
        install_service(sys.executable)


if __name__ == "__main__":
    main()
