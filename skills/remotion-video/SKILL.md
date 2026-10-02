---
name: remotion-video
description: Create, edit, check and render videos with Remotion in ~/remotion (reels, promos, documentaries, music videos, intros, animated text, slideshows). Use it whenever the user asks for a video, reel, clip, animation, intro or montage, mentions Remotion, or wants to change an existing composition.
---

# Making videos with Remotion

You work in the Remotion project at `{{REMOTION_PROJECT}}` through two connectors:
- **remotion-filesystem**: `read_text_file`, `write_file`, `edit_file`, `list_directory`, ...
- **remotion-check**: `check_code`, `describe_media`, `review_frames`, `render_video`.

You cannot see images or run commands. These tools are your eyes. **A video you have not checked with them is not finished**, and you must never claim it works or looks good without a tool saying so.

Talk to the user in their language. Write code, comments and identifiers in English. On-screen text uses the language the user wants for the video.

## 1. The method: always, in this order

1. **Brief.** Subject, format (default: vertical reel 1080x1920, 30 fps), length, tone, material. If something essential is missing (e.g. the exact copy for a promo), ask ONE question. Otherwise decide yourself.
2. **Fidelity to the brief.** First, create `src/<VideoName>/BRIEF.md` containing the user's request **verbatim** (`check_code` compares the video against it).
   - If the user gives a script or copy, it IS the content: keep every point, in the user's order, with the user's numbers, names and quotes exactly as written (true or not is the user's business, not yours). You adapt it to the screen: split it into scenes, break it into short lines, choose the visuals. You never add claims of your own and never drop a point. If it can't all fit on screen in the requested duration, say so in your report; don't silently cut.
   - Respect the requested duration, format and style. If none is given, choose and say so.
   - If the user gave no content, write your own copy, but invent no statistics, quotes or "sources". Never assume who is in a photo.
3. **Material.** Run `describe_media` on every folder of images or audio, including folders outside the project (they get copied into `public/`). Paste its `PhotoInfo` lines into `theme.ts` exactly as given.
4. **Plan, before any code.** Write the shot list into `src/<VideoName>/PLAN.md` (create the folder first) and repeat it briefly in your reply:
   `| # | frames | what we see | exact on-screen text | layout (A-E) | motion |`
   It must follow section 3. Then go straight to the code; don't wait for approval unless the user asked to see the plan first.
   PLAN.md is your memory: long sessions lose old messages. When old messages are removed you receive a WORKSPACE MAP of the files on disk (exports, imports, timeline): trust it. Re-read it before each review round and whenever you are unsure of a file name or a decision, and keep its "open issues" list up to date. Don't re-read source files you haven't changed.
5. **Code.** Follow the structure in section 2. Copy the patterns of `src/Example/`.
6. **`check_code(folder)`, early and often:** after writing the shared files (theme, helpers), then after every 2-3 scenes, not only at the end. Fix every ERROR and run it again until it says NO ERRORS. To find a broken import or type, run `check_code`: never re-read files to verify, because TypeScript tells you exactly what's wrong and where.
7. **`review_frames(composition, brief=...)`**. Fix what it reports (cut or unreadable text first). Run `check_code` again, then `review_frames` with `frames=[...]` on the scenes you changed. The tool allows 4 reviews per composition.
   - Fix with targeted `edit_file` changes to the elements named. **Never rewrite whole scenes after a review**: rewrites bring new defects you cannot check any more.
   - The reviewer can be wrong. If a fix would break a rule of this skill (e.g. pushing text above y=220, leaving half the frame empty), follow the skill and say so in your report.
   - After the last allowed review, change only what you are sure of, then render.
8. **`render_video(composition)`**.
9. **Report.** Give the file path, what each scene shows, and the problems the last review still reported. Never write "perfect" or "all done ✅" if the review found defects.

Think in short steps: decide, then act. Big decisions (scenes, timing, style) are made once, in PLAN.md; revisit them only if a check or review demands it. Long deliberation gets cut off by the reasoning budget and wastes the step.

Do not stop after writing files to ask "shall I check it?". Checking is part of the job. Every turn ends with either a tool call or the final report: never end a turn with only thinking.

## 2. Project structure

```
src/<VideoName>/        PascalCase, a NEW folder per video
  theme.ts              type = loadType(...), colors, photos (PhotoInfo)
  Hook.tsx, ...         ONE scene per file: export const Hook: React.FC = () => ...
  index.tsx             timeline + <Composition>
```
- **Check `src/` first. If a folder with your name already exists, pick another name** (e.g. `LaunchTrailer2`). Never overwrite or reuse an existing video's folder unless the user asks you to edit that video. Existing imports in Root.tsx belong to other videos.
- Register it in `src/Root.tsx` with `edit_file`: add one import line and one `<VideoName />` line. **Never rewrite Root.tsx with write_file**, and never touch other compositions unless asked.
- Composition id = folder name = component name.
- Assets live in `public/<folder>/` and are referenced as `"folder/file.jpg"` (no `public/`).

`theme.ts`:
```ts
import { loadType, type PhotoInfo } from "../kit";
export const type = loadType("documentary");
export const colors = { ink: "#0a0d10", paper: "#efe9df", accent: "#f2a33a" };
export const photos = {
  keeper: { src: "example/keeper.jpg", w: 768, h: 1344, focus: [62, 38] },
} satisfies Record<string, PhotoInfo>;
```

`index.tsx`:
```tsx
const timeline = makeTimeline([
  { len: 100, Comp: Hook },
  { len: 150, Comp: Keeper },
  { len: 110, Comp: EndCard },
]);
const Video: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: colors.ink }}>
    <Scenes timeline={timeline} enter="punch" />
    <LightLeak at={timeline.cuts} />
    <Flash at={timeline.cuts} color={colors.paper} strength={0.5} />
    <Grain opacity={0.3} />
    <ProgressBar color={colors.accent} />
  </AbsoluteFill>
);
export const MyVideo: React.FC = () => (
  <Composition id="MyVideo" component={Video} durationInFrames={timeline.duration}
    fps={30} width={1080} height={1920} />
);
```

A scene (photo in the top two thirds, text below):
```tsx
export const Keeper: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: colors.ink }}>
    <Photo photo={photos.keeper} box={{ left: 0, top: 0, width: 1080, height: 1250 }} zoom={[1, 1.08]} />
    <SafeBlock at={1150}>
      <div style={{ ...type.detail, fontSize: 40, color: colors.accent }}>CAPO NERO — FORTY YEARS</div>
      <div style={{ ...type.body, fontSize: 84, lineHeight: 1.08, color: colors.paper, marginTop: 18 }}>
        <RevealLine delay={18}>Forty years</RevealLine>
        <RevealLine delay={26}>on the same rock.</RevealLine>
      </div>
    </SafeBlock>
  </AbsoluteFill>
);
```
The full example is in `src/Example/` (Hook, Keeper, Logbook, EndCard). Read it when in doubt. Copy its **structure and techniques**, never its palette, texts or comments: choose colors that fit your subject and photos (e.g. pick the accent from a color in the photos).

`describe_media` tells you how much each photo gets enlarged full-screen and the maximum `crop`. Respect it: an over-enlarged photo looks blurry and cheap.

## 3. Direction rules: what separates professional from amateur

**Rhythm**
- The first 2 seconds are the hook: the strongest image or line, big and already moving. Never open on a black screen with a title fading in.
- Scene length: 2-4 s for promos and hooks, 4-6 s for documentary. Every text must stay on screen at least `readFrames(text)`.
- Vary scene lengths. Equal lengths feel mechanical.
- Something always moves. Photos get `zoom` (e.g. `[1, 1.08]`, or `[1.18, 1.04]` for a pull-back). Text enters with `RevealLine`/`Words`. Nothing is frozen for more than 1 s.
- Stagger entrances 6-10 frames apart: kicker, then title, then secondary text.
- Scene exits are handled by `Scenes`. Don't fade every element out by hand.

**Layout (1080x1920)**
- Text stays in the safe area: y from 220 to 1520, x from 72 to 1008. Use `SafeBlock`. The app UI covers the rest.
- Photos are big: full-bleed, or a box at least 60% of the frame. A photo box that doesn't fill the frame ends with `fade={{ side: "bottom", color: colors.ink }}`, never a hard edge.
- No empty band larger than a quarter of the frame. If a photo occupies the top, the text block sits right under its fade, not at the top of the photo. Never a small photo card floating over a blurred copy of itself. Never letterbox bars in a vertical video.
- Every scene uses a different layout, and never the same layout twice in a row:
  - **A** full-bleed photo, scrim, huge title low
  - **B** photo in the top 2/3 (box height ≥ 1250) with `fade`, text starting around y=1150
  - **C** dark photo as texture, giant number or word as the subject
  - **D** typography only, no photo
  - **E** quote: big quote mark, italic body text
- Left-aligned text at the safe margin looks editorial. Center only single short titles.

**Typography**
- One pair per video: `loadType("documentary" | "tech" | "editorial" | "impact" | "elegant")`. Roles: `type.display` for titles, `type.body` for sentences, `type.detail` for kickers, labels and dates.
- Sizes, vertical 1080x1920: hero title 200-260, section title 110-160, sentences 64-90, details 40-48. Nothing under 40.
- Sizes, horizontal 1920x1080: hero title 150-220, section title 100-140, sentences 48-64, details 30-36. Nothing under 30.

**Fill the frame**
- The subject of each scene (a character, an object, a structure, a number) fills 35-60% of the frame height. A small prop in a big empty sky reads as unfinished: move the "camera" closer (scale the world up) instead.
- Illustrated worlds (games, maps, scenes) need foreground, midground and background layers, so the frame has depth and parallax, not one thin strip of ground.
- Break lines yourself with one `RevealLine` per line; never let the browser wrap a title. Max line length: about 10 characters at 250 px display, 18 at 120 px, 22 at 84 px body.
- At most 12 words on screen at once.

**Motion and pacing** (measured by `review_frames` in the PACING section)
- Motion is quick, then still. A single element enters in 10-20 frames (`T.enter`). A group (letters, bars, icons, pixels) assembles in at most 30-45 frames total whatever its size: use `delay = stagger(i, count)`, never a fixed `i * 7`.
- After the last element lands, hold 30-60 frames (`T.hold`) so it can be read, then cut. It must land at least 30 frames before the scene ends: a shape that finishes forming on the cut feels broken.
- Scene length = when the last element lands + hold + reading time. Don't pad scenes: more than ~2.5 s where nothing moves feels like slow motion. A long scene needs a second beat (a new element, a camera move, a change).
- Prefer more short beats to few long scenes: a 60 s video has ~12-18 beats.
- Entrances use `ease` (fast start, soft landing) or springs with `damping` 12-20. `easeInOut` and linear are for moves from A to B, not for entrances.
- Background drift (slow zoom, floating particles) may be slow, but it is not a beat: it doesn't make a static scene feel alive.

**Color**
- Background, one text color and ONE accent, all defined in `theme.ts`. The accent goes on one word or one line per scene, never everywhere.
- Text over a photo always gets a `Scrim` behind it, or sits on a solid area of the frame.

**Texture and transitions**
- `Grain` (0.25-0.4) for cinematic or documentary. `LightLeak` and/or `Flash` at `timeline.cuts`. `Vignette` is optional. No more than these.

**Banned (amateur tells)**: system fonts (Arial, Georgia...), emoji, neon text-shadow glow, rainbow gradients, a gold line under every title, everything centered, fade-in as the only animation, letterbox bars, identical scenes, tiny text, placeholder text, more than one accent color.

## 4. Remotion technical rules

- Every animated value comes from `useCurrentFrame()`. No `useState`, `useEffect`, timers, CSS `transition`/`animation`, or Tailwind `animate-*`.
- `spring({ frame, fps, ... })` with `const { fps } = useVideoConfig()`. Never hardcode fps.
- `interpolate(frame, [a, b], [x, y], clamp)` with `clamp` from the kit when the input is a frame.
- Inside a `Sequence` (every scene), `useCurrentFrame()` starts at 0 and `useVideoConfig().durationInFrames` is the scene length.
- Photos: use `<Photo>`. If you use `<Img>` directly: `src={staticFile("folder/file.jpg")}` and `maxWidth: "none"` in its style (Tailwind would squash it).
- Video: `<OffthreadVideo>`. Audio: `<Audio src={staticFile("folder/song.mp3")} />` once in `index.tsx`. Make the timeline match the duration `describe_media` reports.
- Randomness: `random("seed")` from remotion, never `Math.random()`.
- Apostrophes in JSX text: `{"Don't stop"}` or `Don&apos;t stop`.
- `AbsoluteFill` is a flex column. For precise layout use `position: "absolute"` with px values.

## 5. Kit reference: `import { ... } from "../kit"`

- `loadType(pair)` → `{ display, body, detail }` CSS objects: spread them `{ ...type.display, fontSize: 200 }`.
- `Photo { photo: PhotoInfo, box?: {left, top, width, height}, zoom?: [from, to], crop?: number, drift?: [fromPx, toPx], filter?: string, radius?: number, fade?: { side, color } }`: always fills its box, keeps `focus` in frame, moves over the scene. `crop` > 1 tightens on the focus point.
- `RevealLine { delay, style? }`: one line rising from a mask.
- `Words { text, delay?, stagger?, accent?: string[], accentColor?, style? }`: word-by-word entrance with blur.
- `Typewriter { text, delay?, cps?, style? }`, `Counter { to, from?, delay?, duration?, format?, style? }`.
- `Captions { lines: {from, to, text, accent?}[], top, accentColor?, style? }`: subtitles or narration. Place it in `index.tsx` outside the Scenes (absolute frames).
- `SafeBlock { at, anchor?: "top" | "bottom", align?: "left" | "center", style? }`, `useSafe()` → `{ top, bottom, left, right, width }`.
- `Scrim { side?: "top" | "bottom", size?, color? }`, `Vignette { strength? }`, `Grain { opacity? }`, `Flash { at, color?, strength? }`, `LightLeak { at, color? ("r,g,b") }`, `ProgressBar { color, height? }`, `useShake(hits, strength?)` → `{ x, y }`.
- `makeTimeline([{ len, Comp }])` → `{ scenes, cuts, duration }`. `Scenes { timeline, enter?: "punch" | "fade" | "cut" }`.
- Helpers: `clamp`, `ease`, `easeInOut`, `prog(frame, a, b)` (0→1), `fadeInOut(frame, a, b, len?)`, `sec(s)`, `readFrames(text)`.
- Timing: `T = { fast: 8, enter: 14, build: 36, hold: 36 }`, `stagger(i, count, total?)` → delay of item i so the whole group starts within `total` frames.


## 6. Editing an existing video

Read the files involved first. Change only what was asked, with `edit_file`. Then `check_code`, `review_frames` on the affected frames, and `render_video`. Describe exactly what you changed.
