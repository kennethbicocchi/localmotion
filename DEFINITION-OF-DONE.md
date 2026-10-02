# Definition of done

The project is finished when a local model, on one 24 GB GPU, turns a one-paragraph brief into a video that could be published, unattended, and the user gets the result wherever they are. Each criterion below is measurable; most are measured automatically by `remotion-check`, the rest by a reviewer watching the video.

## Acceptance test

**5 complex briefs in a row**, run unattended through the Telegram bot, each 45-60 s, each demanding real animation (no slideshows): for example a game-style presentation, a racing-game HUD intro, a space-sim product launch, a music video synced to an audio track, a data story told through a game mechanic. They are not tuned for and not cherry-picked.

## 1. Reliability: it always delivers

| Criterion | Target |
|---|---|
| Briefs that end with a rendered video, no human help | ≥ 4 of 5 (the 5th must at least reach the auto-render) |
| Results that reach Telegram, success or failure | 5 of 5: no silent outcome, ever |
| Videos that crash on render, or a render that fails without explanation | 0 |
| Production time for 60 s, at 260 W | ≤ 90 min |
| Silent stops needing a manual "continua" | 0 (automatic nudges allowed) |

## 2. Fidelity to the brief

The user's content is the content: whether their figures are true is their business. The model adapts it to the screen and never adds to it or drops from it. Measured by `check_code` against `BRIEF.md` (the request saved verbatim) plus a reviewer.

| Criterion | Target |
|---|---|
| User's figures, names and quoted lines missing from the video | 0 (or explicitly reported as not fitting) |
| Claims or figures added to a user's script | 0 |
| Requested duration | ±10% |
| Requested format (vertical / horizontal) and style | respected |
| Order of a user's script | preserved |
| Without user content: invented statistics, quotes or "sources" | 0 |
| Final report matches the last review (no "perfect" over known defects) | 5 of 5 |

## 3. Visual quality (reviewer score, 1-10, same rubric as `review_frames`)

| Criterion | Target |
|---|---|
| Average score | ≥ 7 |
| Worst video | ≥ 6 |
| Text cut off, overflowing, or beyond the safe area | 0 in the final video |
| Empty bands over 30% of the safe area | 0 (deliberate typographic pauses excepted) |
| Distinct layouts per video | ≥ 3, never the same layout twice in a row |
| Typography and palette | one font pair, one accent, consistent throughout |

## 4. Motion and pacing (measured by the PACING section and `check_code`)

| Criterion | Target |
|---|---|
| FROZEN scenes (nothing moves for more than 2.5 s) | 0 |
| SLOW scenes (only drift for more than 3.5 s) | ≤ 1 per video |
| Last element landing less than 30 frames before the cut | 0 |
| Entrance longer than 45 frames (background drift excepted) | 0 |
| Transitions between style acts | designed (wipe, morph, flash, camera move), not plain cuts |

## 5. Code

| Criterion | Target |
|---|---|
| `check_code` at render time | NO ERRORS |
| Uses the kit (`loadType`, `makeTimeline`, `Photo`…) | yes |
| Orphan or duplicated files | 0 |
| Other compositions touched | 0 |

## 6. Remote workflow

| Criterion | Target |
|---|---|
| `/video` confirmed on Telegram | within 1 minute while the PC is awake |
| Progress messages | start, every review score, final result |
| `/status` | always accurate, including runs started outside the bot |
| PC stays awake during a job; back to normal power after | yes |
| Wake from sleep for a remote `/video` | **open: user's choice** between periodic wake (A) and Wake-on-LAN (B) |

## 7. Bionic integration

| Criterion | Target |
|---|---|
| Skill installed, `remotion-check` connected, model at 72k with vision | yes |
| One complex video made end to end inside Bionic | yes, delivered to Telegram |

## 8. Repository

English only, README with install steps, no secrets in the repo (tokens live outside it, chmod 600), `.gitignore` for jobs and logs, a license chosen by the user.
