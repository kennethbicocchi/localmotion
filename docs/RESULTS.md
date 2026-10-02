# Results

All runs were on one RTX 3090 (power capped at 260 W), LM Studio, unattended. Scores are 1-10. *Reviewer* is the vision model inside `review_frames`; *human* is a person watching the final video.

## Showcase runs (final agent loop, Qwen 3.8 27B, effort medium, 72k context)

| Brief | Length / format | Outcome | Time | Reviewer | Human | Notes |
|---|---|---|---|---|---|---|
| NEON DRIFT, racing-game trailer | 45 s, 9:16 | ✅ rendered | 60 min | 6, 6, 6 | 7 | Full HUD, split-screen duel, podium; every figure from the brief on screen |
| Blockwise, sandbox-game pitch | 60 s, 16:9 | ✅ rendered | 95 min | 3, 6, 6 | 6 | Isometric voxel world, crafting grid, night with torches, achievements; elements a bit small for 16:9 |
| ORBITAL, space-sim launch | 50 s, 16:9 | ✅ rendered (2nd attempt) | 86 min | 7, 6 | 6.5 | Mission-control HUD, wireframe Earth, telemetry, docking; all brief content on screen. The 1st attempt was cut by the reasoning budget mid-thought (auto-rendered, incomplete), which led to the "sent back to work" recovery |
| localmotion promo | 45 s, 16:9 | ✅ rendered | 57 min | 7, 5, 7 | 7 | Terminal hook, GPU chip, four steps, 0/0/1 counters, the sample videos in device frames; soundtrack added afterwards by a human |

## Model comparison (same 60 s, three-style brand film; earlier agent loop, 48k context)

| Model | Rendered video | Steps / time | Human score | What happened |
|---|---|---|---|---|
| Qwen 3.6 27B | ❌ render crash | 120 / ~53 min | ~5 | Ambitious design; a loop-dependent animation range crashed and was never found; invented figures with a fake source line |
| **Qwen 3.8 27B** | ✅ | 87 / 86 min | **~7** | Consistent brand system, real 3D gems, honest report |
| Swift 1.5 (Qwen 3.8 fine-tune) | ❌ out of context | 23 / 16 min | n/a | The most ambitious plan and clean code, but it filled 48k before assembling the video |
| Gemma 4 12B | ❌ | 37 / ~6 min | n/a | Looped on its errors, never reviewed or rendered, then claimed the video was ready |

## Before and after the tools (same model family, 30 s documentary reel with photos)

| | Model alone | With localmotion |
|---|---|---|
| Typography | system font | a font pair, clear hierarchy |
| Photos | small 16:9 cards with letterbox bars | full-bleed, focused on faces |
| Text | captions cut off by the frame | inside the safe area |
| Facts | invented | none invented |
| Final report | "✅ all done" | quotes its own review score |
| Human score | ~2 | ~6 |

## What moved the needle (in order of impact)

1. **Context management.** Every model failed long videos at 48k with full history. What fixed it: an 8-bit KV cache (48k → 72k), compacting old file contents and reasoning, a workspace map of the files on disk, and PLAN.md as the model's memory.
2. **Reasoning effort `medium`.** About half the thinking per step: faster runs, less context used, no visible loss of quality.
3. **Recovery from silent stops.** Local models sometimes end a turn mid-task, especially when a reasoning budget cuts them off. The agent loop sends them back to work.
4. **Readable errors.** A render crash reported as `bundle.js:84427` sent the model hunting in other projects; reporting the error message and the scene fixed it immediately.
5. **Measuring instead of asking.** Vision models misjudge positions and can't see motion. Pixel measurements (empty bands, frozen scenes) and static timing rules catch those reliably.
6. **The kit and the example.** Models imitate far better than they invent. The example must itself follow every rule: it once contained an invented date, and that would have been copied.
