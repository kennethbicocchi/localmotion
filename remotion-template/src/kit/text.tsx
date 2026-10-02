import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, ease } from "./time";

// One line of text rising from behind a mask. Several lines = several RevealLines,
// with delays staggered by 6-10 frames.
export const RevealLine: React.FC<{
  delay: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ delay, children, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: { damping: 200 }, durationInFrames: 20 });
  return (
    <div style={{ overflow: "hidden", padding: "0 0.12em 0.14em 0", marginBottom: "-0.14em", ...style }}>
      <div style={{ transform: `translateY(${(1 - p) * 115}%)` }}>{children}</div>
    </div>
  );
};

// Sentence that enters word by word, with blur. accent = words to color.
export const Words: React.FC<{
  text: string;
  delay?: number;
  stagger?: number; // frames between one word and the next
  accent?: string[];
  accentColor?: string;
  style?: React.CSSProperties;
}> = ({ text, delay = 0, stagger = 2, accent = [], accentColor, style }) => {
  const frame = useCurrentFrame();
  return (
    <div style={style}>
      {text.split(" ").map((w, i) => {
        const t = interpolate(frame, [delay + i * stagger, delay + i * stagger + 10], [0, 1], {
          ...clamp,
          easing: ease,
        });
        const clean = w.replace(/[.,;:!?…"“”]/g, "");
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              marginRight: "0.26em",
              opacity: t,
              transform: `translateY(${(1 - t) * 0.3}em)`,
              filter: `blur(${(1 - t) * 6}px)`,
              color: accent.includes(clean) ? accentColor : undefined,
            }}
          >
            {w}
          </span>
        );
      })}
    </div>
  );
};

// Typed text with a blinking cursor. cps = characters per second.
export const Typewriter: React.FC<{
  text: string;
  delay?: number;
  cps?: number;
  style?: React.CSSProperties;
}> = ({ text, delay = 0, cps = 24, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const n = Math.max(0, Math.floor(((frame - delay) / fps) * cps));
  const cursor = frame % 16 < 8 ? 1 : 0;
  return (
    <div style={style}>
      {text.slice(0, n)}
      <span style={{ opacity: cursor }}>▍</span>
    </div>
  );
};

// Number counting from `from` to `to`. format decides how it is written.
export const Counter: React.FC<{
  to: number;
  from?: number;
  delay?: number;
  duration?: number; // frames
  format?: (n: number) => string;
  style?: React.CSSProperties;
}> = ({ to, from = 0, delay = 0, duration = 40, format = (n) => Math.round(n).toLocaleString("en-US"), style }) => {
  const frame = useCurrentFrame();
  const t = interpolate(frame, [delay, delay + duration], [0, 1], { ...clamp, easing: ease });
  return <div style={{ fontVariantNumeric: "tabular-nums", ...style }}>{format(from + (to - from) * t)}</div>;
};

// Subtitles or narration: one line at a time, during frames [from, to).
// Place it at the top level of the video (not inside a Sequence): frames are absolute.
export type Caption = { from: number; to: number; text: string; accent?: string[] };

export const Captions: React.FC<{
  lines: Caption[];
  top: number; // px from the top: inside the safe area
  accentColor?: string;
  style?: React.CSSProperties; // font, color, size
}> = ({ lines, top, accentColor, style }) => {
  const frame = useCurrentFrame();
  const line = lines.find((l) => frame >= l.from && frame < l.to);
  if (!line) {
    return null;
  }
  const out = interpolate(frame, [line.to - 8, line.to], [1, 0], clamp);
  return (
    <div style={{ position: "absolute", left: 80, right: 80, top, opacity: out }}>
      <Words
        key={line.from}
        text={line.text}
        delay={line.from}
        accent={line.accent}
        accentColor={accentColor}
        style={style}
      />
    </div>
  );
};
