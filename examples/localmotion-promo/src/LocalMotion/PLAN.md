# Plan — LocalMotion promo (1920x1080, 30fps, 1350f)

Safe area (horizontal): x 115–1805, y 76–1004.

| # | frames | what we see | exact on-screen text | layout (A-E) | motion |
|---|--------|-------------|---------------------|--------------|--------|
| 1 | 120 | Terminal prompt typed, question punches in, glitch bars | `localmotion@gpu:~$` prompt · "What if your videos cost 0 tokens?" (0 tokens? in accent) | D typography | prompt Typewriter, 3 RevealLines, glitch slices, grid bg |
| 2 | 180 | "localmotion" huge left, sentence words-in; GPU chip right pulsing rings | "localmotion:" · "Motion-design videos made by an open model on your own GPU." (accent: open model) | D + prop | Words blur-in stagger 1; chip spring + looping glow rings |
| 3 | 110 | Terminal window right, brief typed line by line | "STEP 01" · "Write a brief." + typed brief lines in window | B split | heading RevealLine; Typewriter brief; cursor |
| 4 | 110 | Code editor right: code lines grow, footer "tokens used: 0", preview bar sweeps | "STEP 02" · "The model writes the video as code." + footer "tokens used: 0" | B split | lines grow staggered, playhead sweep, footer pop |
| 5 | 130 | 2x2 grid of real sample frames, scan bar sweeps, checkmarks pop | "STEP 03" · "It checks its work and looks at every frame." + "frame 240/240 ok" | B split | scan bar left→right, checks stagger, grid tiles drift |
| 6 | 120 | Phone frame right, chat bubble "Your video is ready" slides in with thumb | "STEP 04" · "The finished video lands on your phone." + "Your video is ready" | B split | phone spring up, bubble slide+settle, thumb zoom |
| 7 | 150 | Three giant numbers on dark grid | "0" TOKENS (counter from 128000 stuck at 0) · "0" API BILLS (counter) · "1" GPU | C giant numbers | counters count down, pop scale, stagger 20f |
| 8 | 250 | Floating devices: 2 phones + monitor, playhead bars running, captions | "PROOF" · "a racing-game trailer" · "a sandbox-game pitch" · "a lighthouse short film" | A devices | spring entrances staggered, sin() bob, progress bars, slight tilt |
| 9 | 180 | Wordmark + tagline over grid with green glow | "localmotion" · "Open source." · "Your GPU, your videos." (accent line 2) | D typography | wordmark Words-in, rule line grows, tagline RevealLines |

Transitions: enter="cut" + Flash (green) + Glitch slice bursts at timeline.cuts. Grain 0.25, Vignette 0.4, ProgressBar green.

Photos (public/localmotion-promo):
- racingDuel 540x960 focus[50,50] → proof phone L, check-grid
- racingHud 540x960 focus[50,95] → proof phone? no: phone L uses duel; bubble thumb + check-grid
- sandboxNight 960x540 focus[50,50] → proof monitor
- lighthouseTitle 270x480 focus[48,38] → proof phone R
