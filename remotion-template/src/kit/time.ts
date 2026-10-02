import { Easing, interpolate } from "remotion";

export const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// ease: soft entrances (fast start, settles). easeInOut: moves from A to B
export const ease = Easing.bezier(0.22, 1, 0.36, 1);
export const easeInOut = Easing.bezier(0.65, 0, 0.35, 1);

// 0 -> 1 between frames a and b
export const prog = (frame: number, a: number, b: number, easing = ease) =>
  interpolate(frame, [a, b], [0, 1], { ...clamp, easing });

// 0 -> 1 -> 0: in over [a, a + len], out over [b - len, b]
export const fadeInOut = (frame: number, a: number, b: number, len = 10) =>
  interpolate(frame, [a, a + len, b - len, b], [0, 1, 1, 0], clamp);

export const mix = (a: number, b: number, t: number) => a + (b - a) * t;

// Seconds -> frames
export const sec = (s: number, fps = 30) => Math.round(s * fps);

// Minimum frames for a text to be readable: 0.3 s per word + 1 s, at least 1.5 s
export const readFrames = (text: string, fps = 30) => {
  const words = text.trim().split(/\s+/).length;
  return Math.round(Math.max(1.5, words * 0.3 + 1) * fps);
};

// Standard durations in frames (30 fps). Motion should feel snappy, then hold still to be read.
export const T = {
  fast: 8, // small accents, flashes, pops
  enter: 14, // a single element entering
  build: 36, // a whole group (letters, bars, icons) assembling: never longer
  hold: 36, // stillness after the last element lands, before the cut
};

// Delay of item i when `count` items must all start within `total` frames.
// Keeps a build the same length whether it has 5 letters or 50.
export const stagger = (i: number, count: number, total: number = T.build - T.enter) =>
  count <= 1 ? 0 : Math.round((i * total) / (count - 1));
