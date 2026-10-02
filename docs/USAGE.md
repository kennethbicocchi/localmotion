# Using localmotion

Install first ([INSTALL.md](INSTALL.md)). This page covers daily use: making videos, writing good briefs, starting and stopping the system, and fixing common problems.

## Three ways to make a video

### 1. From your phone, with the Telegram bot (recommended)

Send your bot `/video` followed by the brief:

```
/video A 30-second vertical reel for my bakery "Crumb & Co": open on fresh bread coming out of the oven,
then three products with prices (sourdough €4.50, croissant €1.80, focaccia €3.20), end with
"Open every day from 7 am — Via Roma 12". Warm, cozy, handmade feel.
```

To use your own photos, music or clips, attach them and write the `/video …` brief **as the caption** (select several photos and send them as an album; the caption goes on the album). Supported: JPG, PNG, WebP, MP3, WAV, M4A, OGG, MP4, MOV, WebM. Telegram compresses photos; send them as *files* to keep the full resolution.

What you get back:

| When | Message |
|---|---|
| Right away | "Video #… starting" (or "queued, position N" if another one is running) |
| When the model starts | "started with qwen/qwen3.8-27b" |
| After each visual review | "review 1 → 6/10", "review 2 → 7/10", … |
| At the end | the **video**, a **contact sheet** of frames and the **agent's report** (what it made, what it fixed, what it couldn't verify) |
| If it fails | the reason, and an auto-rendered version if the code was clean but the agent stopped before rendering |

All commands:

| Command | What it does |
|---|---|
| `/video <brief>` | Start a video, or queue it if one is running. Videos run one at a time, with a 10-minute GPU cool-down between queued ones. |
| `/status` | What's running: elapsed time, step (out of 120), context used, review scores, queue, GPU temperature and power. Also reports videos started outside the bot. |
| `/cancel` | Stop the running video. |
| `/last` | Send the last finished video again. |
| `/model` | Show the model for new videos and the vision models available. `/model <id>` changes it. |
| `/help` | The command list. |

Only your chat is obeyed: messages from anyone else are ignored.

### 2. From the command line

```sh
agent/run_agent.py "$(cat my-brief.txt)" --model qwen/qwen3.8-27b --effort medium --log run.jsonl
```

| Option | Meaning |
|---|---|
| `--model` | LM Studio model id (must be loaded, with vision) |
| `--effort` | reasoning effort: `none`, `low`, `medium` (recommended), `high` |
| `--max-steps` | step budget (default 80; the bot uses 120 for long videos) |
| `--log` | JSONL log of every step, tool call and result |
| `--resume` | continue a previous run from its log |

The script uses the project in `REMOTION_PROJECT` (the bundled template by default) and prints each step as it goes.

If the bot is running, you can also drop a text file containing the brief into `jobs/inbox/`. It's picked up within half a minute, queued like a `/video`, and the result goes to Telegram.

### 3. In a chat with the model (LM Studio / Bionic)

Open a chat with the model, enable the `remotion-filesystem` and `remotion-check` MCP servers, and ask for a video in plain words. The skill is loaded automatically when you mention a video, reel, clip or Remotion; you can also say "use the remotion-video skill".

This is good for short videos and for iterating together ("make the title bigger", "slow down scene 3"). For long, complex videos prefer the bot: it adds history compaction, recovery from silent stops and the auto-render safety net. If the model stops mid-task in a chat, type "continue". Rendered videos are sent to Telegram from chats too.

## Writing a good brief

The model is faithful to what you write, and it's checked automatically.

- **Say the format and length:** "45 seconds, vertical 9:16" or "60 seconds, 16:9". Default: vertical 1080×1920.
- **Put your exact content in quotes or a list:** taglines, numbers, names, dates, prices. Your figures appear on screen exactly as written; the model adds no figures of its own.
- **If you have a script, paste it.** It will be adapted to the screen (split into scenes and short lines), never cut silently or extended with invented claims.
- **Describe the feeling and give visual ideas** ("feels like real gameplay with a HUD", "documentary, warm, slow"); the model invents the rest.
- **Ask for what's hard, not slides:** worlds, HUDs, transitions, characters. The tools are built for that.
- **One video per brief.** To change an existing video, ask in a chat, or send a new brief that names the video.

Examples in [examples/briefs/](../examples/briefs/).

## Where things end up

| What | Where |
|---|---|
| Finished videos | `<project>/out/<VideoName>.mp4` (and on Telegram) |
| The video's source | `<project>/src/<VideoName>/`: one file per scene, plus `BRIEF.md` (your request) and `PLAN.md` (the model's plan) |
| Frames checked by the reviewer | `<project>/out/check/`, including `<VideoName>-contact-sheet.jpg` |
| Files you sent from Telegram | `<project>/public/tg-<job id>/` |
| Logs of bot jobs | `jobs/<job id>/` (`brief.txt`, `run.out`, `run.jsonl`) |

You can open `<project>` in Remotion Studio (`npx remotion studio`) to scrub through any video or tweak it by hand.

## Starting, stopping, after a reboot

| Piece | How |
|---|---|
| Telegram bot | Starts at login (systemd user service). It sends "localmotion bot is online" when it starts. `systemctl --user stop qwen-video-bot` / `start` / `restart` / `status`; logs: `journalctl --user -u qwen-video-bot -f` |
| LM Studio + model | Nothing to do: on a `/video` the bot starts LM Studio headless if needed (`lms daemon up`, `lms server start`) and loads the model with the right settings |
| Sleep | The PC is kept awake only while a video is being made |
| GPU power limit | `nvidia-smi -pl` resets at reboot; make it permanent with a small systemd service (see below) |

The bot runs only while you're logged in. To make it survive a reboot without anyone logging in, enable automatic login or lingering for your user (`loginctl enable-linger <user>`); LM Studio then starts headless when needed.

Permanent 260 W power limit for an RTX 3090 (run once):

```sh
sudo bash -c 'printf "[Unit]\nDescription=GPU power limit\nAfter=multi-user.target\n\n[Service]\nType=oneshot\nExecStart=/usr/bin/nvidia-smi -pm 1\nExecStart=/usr/bin/nvidia-smi -pl 260\n\n[Install]\nWantedBy=multi-user.target\n" > /etc/systemd/system/gpu-power-limit.service && systemctl enable --now gpu-power-limit.service'
```

## Troubleshooting

| Problem | Cause and fix |
|---|---|
| The model fails to load ("failed to allocate buffer", out of memory) | The vision adapter and the context don't fit. Close apps using the GPU (video players, games, hardware-accelerated browsers), turn off the MTP draft, or use 49152 context. The bot falls back to 48k automatically. |
| `describe_media` / `review_frames` say "vision unavailable" | The loaded model has no vision: download its `mmproj` file into the same folder and reload. |
| The bot doesn't answer | `systemctl --user status qwen-video-bot` and `journalctl --user -u qwen-video-bot -n 50`. Check `~/.config/qwen-video-bot/config.json` and that you're messaging from the chat used during setup. Only one program at a time can read the bot's messages: stop any other copy. |
| `/status` says idle but the GPU is busy | `/status` also reports videos started outside the bot (command line); if it still says idle, LM Studio is serving another app (e.g. a chat). |
| Render fails with `Failed to fetch` / `ERR_ADDRESS_UNREACHABLE` on fonts.gstatic.com | Fonts load from Google Fonts at render time and need internet. Retry; if your IPv6 is flaky, prefer IPv4. |
| A video "finishes" without rendering | The agent loop sends the model back to work (up to 3 times). If it still stops, the bot auto-renders the composition when its code is clean and tells you it did. |
| Videos take long | Normal: 60-95 min for complex 60 s videos, mostly model thinking. `effort: medium` (bot config) roughly halves the thinking compared to the model's default. |
| The video ignores part of the brief | Look at the FIDELITY lines in `jobs/<id>/run.out`: they list figures or quotes from the brief missing on screen. Put must-have content in quotes or a list. |
| GPU too hot or loud | Cap the power (`sudo nvidia-smi -pl 260` on a 3090: about 6 °C cooler, quieter, a few % slower). |

## Settings

`~/.config/qwen-video-bot/config.json` (written by `setup_bot.py`):

| Key | Default | Meaning |
|---|---|---|
| `token_file` | set by setup | file holding the bot token (`chmod 600`) |
| `chat_id` | set by setup | the only chat the bot obeys |
| `model` | `qwen/qwen3.8-27b` | model for new videos (also `/model <id>`) |
| `effort` | model default | reasoning effort for the agent: `medium` recommended |

Environment variables: `REMOTION_PROJECT` (the Remotion project; default: the bundled template), `LMSTUDIO_URL` (default `http://127.0.0.1:1234`), `LMS_BIN` (path of `lms`), `VIDEO_MODEL`, `QWEN_TELEGRAM_NOTIFY=0` (don't send renders to Telegram).
