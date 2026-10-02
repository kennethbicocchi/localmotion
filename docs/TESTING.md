# Testing

Three levels, from seconds to hours.

## 1. Unit tests: seconds, no model

```sh
remotion-check/.venv/bin/python -m pytest tests -q
```

Each test builds a tiny fake Remotion project and checks that the rules react: classic mistakes (`Math.random`, `spring` without `fps`, loop-dependent animation ranges that crash, system fonts, `<img>`), timing warnings (slow staggers, animations landing on the cut), fidelity to the brief (missing user figures, invented ones, split quotes), timeline parsing, the empty-band measurement and the agent loop's history compaction.

## 2. Smoke test: about a minute

```sh
./scripts/smoke_test.sh
```

It runs the unit tests, runs `check_code` on the example video, renders three real frames with Remotion, and asks the loaded vision model to describe a photo.

## 3. Acceptance test: the real thing

What it takes to call the project done is written down in [DEFINITION-OF-DONE.md](../DEFINITION-OF-DONE.md). In short: **5 complex briefs in a row, unattended**, each 45-60 s and demanding real animation. At least 4 of 5 must end with a rendered video, every result must reach the user, with a reviewer average of at least 7/10, no frozen scenes and fidelity to the brief.

Run a brief:

```sh
agent/run_agent.py "$(cat examples/briefs/neon-drift-racing-trailer.txt)" \
  --model qwen/qwen3.8-27b --effort medium --max-steps 120 --log run.jsonl
```

Or through the bot: `/video …` on Telegram, or a text file in `jobs/inbox/`.

The log (`run.jsonl`) records every step: tool calls, results, token usage, review scores. Things to look at:
- the review scores and the **PACING** and **FIDELITY** sections in the tool results;
- `(compacted …)` lines: context management at work;
- `(sent back to work …)` and `(empty turn …)`: recoveries from silent stops;
- the final report: does it match the last review?

`examples/briefs/` holds the briefs behind the showcased videos. Write new ones that are hard in different ways (gameplay, data, characters, music sync), never only slides.
