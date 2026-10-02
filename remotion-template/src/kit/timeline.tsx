import React from "react";
import { AbsoluteFill, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp } from "./time";

export type SceneDef = { len: number; Comp: React.FC };

// Computes each scene's start, the cuts and the total duration from the lengths alone.
// Take the Composition's duration from here, so it is never wrong.
export const makeTimeline = (scenes: SceneDef[]) => {
  let from = 0;
  const placed = scenes.map((s) => {
    const p = { ...s, from };
    from += s.len;
    return p;
  });
  return { scenes: placed, cuts: placed.slice(1).map((s) => s.from), duration: from };
};

export type Timeline = ReturnType<typeof makeTimeline>;

// Scene entrance. punch: small zoom that settles (rhythm, promos). fade: dissolve (calm).
// cut: hard cut (pair it with Flash or LightLeak on the cuts).
const Shell: React.FC<{ enter: "punch" | "fade" | "cut"; children: React.ReactNode }> = ({ enter, children }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  if (enter === "cut") {
    return <AbsoluteFill>{children}</AbsoluteFill>;
  }
  if (enter === "fade") {
    const opacity = interpolate(frame, [0, 10, durationInFrames - 10, durationInFrames], [0, 1, 1, 0], clamp);
    return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>;
  }
  const p = spring({ frame, fps, config: { damping: 18, stiffness: 160 } });
  const out = interpolate(frame, [durationInFrames - 5, durationInFrames], [1, 0.55], clamp);
  return (
    <AbsoluteFill style={{ transform: `scale(${interpolate(p, [0, 1], [1.07, 1])})`, opacity: out }}>
      {children}
    </AbsoluteFill>
  );
};

// Lays out the timeline's scenes, each in its own Sequence.
// Inside each scene useCurrentFrame() starts again from 0.
export const Scenes: React.FC<{ timeline: Timeline; enter?: "punch" | "fade" | "cut" }> = ({
  timeline,
  enter = "punch",
}) => (
  <>
    {timeline.scenes.map(({ from, len, Comp }) => (
      <Sequence key={from} from={from} durationInFrames={len}>
        <Shell enter={enter}>
          <Comp />
        </Shell>
      </Sequence>
    ))}
  </>
);
