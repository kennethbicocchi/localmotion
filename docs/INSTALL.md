# Install

Tested on Linux (CachyOS) with an RTX 3090 24 GB, LM Studio (Bionic edition), Node.js 26 and Python 3.12 with uv. macOS and Windows/WSL should work for everything except the systemd service of the Telegram bot.

## 1. The model

In LM Studio, download **Qwen 3.8 27B, Q4_K_M** (~17 GB) and its vision adapter **`mmproj-…`** (~0.9 GB) into the same folder. Without the mmproj file the model is text-only, and the tools that look at images (`describe_media`, `review_frames`) lose their eyes. Check in LM Studio that the model shows the vision badge.

### Fitting a 27B model, vision and a long context into 24 GB

Context is what makes long videos fail, so get as much as fits:

| Setup | Context that fits next to the vision adapter |
|---|---|
| Default (16-bit KV cache, MTP draft on) | ~48k (49152) |
| **8-bit KV cache, MTP draft off** | **~72k (73728)**, recommended |

In the model's load settings in LM Studio: enable **Flash Attention**, set **K cache** and **V cache quantization** to **q8_0**, turn off **speculative decoding (MTP draft)**, and set the context length to **73728**, parallel sessions to **1**. From the command line:

```sh
lms load <model-id> -c 73728 --parallel 1 --gpu max --no-speculative-draft-mtp
```

If other apps hold VRAM (video players, games, browsers with hardware acceleration), 72k may not fit: use 49152. The Telegram bot falls back to it automatically.

**Heat.** A video keeps the GPU busy for an hour or more. Capping the power costs little speed, because generation is memory-bound: `sudo nvidia-smi -pl 260` on a 3090 brought the temperature from 81 to 75 °C and the fans from 100% to 75%. The setting resets on reboot.

## 2. localmotion

```sh
./install.sh
```

It checks the requirements, creates the Python environment of the check server, installs the Remotion template (`remotion-template/`), installs the skill into `~/.lmstudio/skills/remotion-video/` with your project path, and prints the MCP configuration.

To use your own Remotion project instead of the template: `REMOTION_PROJECT=~/my-remotion ./install.sh`. It copies `kit/` and `Example/` into it (never overwriting) and tells you how to register the example.

## 3. Connect the tools to LM Studio

Add the two servers printed by `install.sh` to `~/.lmstudio/mcp.json` under `"mcpServers"`:

- **remotion-filesystem**: read/write access limited to the Remotion project.
- **remotion-check**: `check_code`, `describe_media`, `review_frames`, `render_video`.

Reviews and renders take minutes, so keep the long timeout. In the **Bionic** edition, add the same two servers from its MCP settings (or its `ng-mcp.json`, with the app closed).

## 4. Check the installation

```sh
./scripts/smoke_test.sh
```

All four steps should pass: unit tests, `check_code` on the example, a real render of three frames, and the vision model describing a photo (this one is skipped if no vision model is loaded).

## 5. Optional: the Telegram bot

Make videos from your phone, follow the progress and get the result, wherever you are.

```sh
cd telegram_bot
REMOTION_PROJECT=<your project, if not the template> ../remotion-check/.venv/bin/python setup_bot.py --install-service
```

The wizard walks you through it:
1. create a bot with @BotFather;
2. paste its token (hidden input, stored with `chmod 600` in `~/.config/qwen-video-bot/`);
3. send your bot a message: from then on it obeys only your chat.

`--install-service` runs it as a systemd user service that starts at login.

Commands: `/video <brief>` (attach photos, audio or video with `/video …` as the caption), `/status`, `/cancel`, `/last`, `/model [id]`, `/help`. Settings in `~/.config/qwen-video-bot/config.json`: `model` (default `qwen/qwen3.8-27b`) and `effort` (`medium` recommended: about half the thinking time, with no visible loss in our runs).

During a job the bot keeps the PC awake. Videos started elsewhere (the command line, the inbox folder) are reported too. Every `render_video`, also from an LM Studio chat, sends the video to Telegram; set `QWEN_TELEGRAM_NOTIFY=0` to turn that off.
