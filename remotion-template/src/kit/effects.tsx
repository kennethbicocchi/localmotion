import React from "react";
import { AbsoluteFill, interpolate, random, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp } from "./time";

// Film grain: on top of everything, once, in index.tsx
export const Grain: React.FC<{ opacity?: number }> = ({ opacity = 0.35 }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ mixBlendMode: "overlay", opacity, pointerEvents: "none" }}>
      <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <filter id="kit-grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves={2} seed={frame % 16} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#kit-grain)" />
      </svg>
    </AbsoluteFill>
  );
};

// Darkened edges: pulls the eye to the center
export const Vignette: React.FC<{ strength?: number }> = ({ strength = 0.6 }) => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,${strength}) 100%)`,
      pointerEvents: "none",
    }}
  />
);

// Dark gradient from one side, to make text over a photo readable
export const Scrim: React.FC<{ side?: "top" | "bottom"; size?: number; color?: string }> = ({
  side = "bottom",
  size = 900,
  color = "rgba(0,0,0,0.85)",
}) => (
  <div
    style={{
      position: "absolute",
      left: 0,
      right: 0,
      [side]: 0,
      height: size,
      background: `linear-gradient(to ${side}, transparent, ${color})`,
      pointerEvents: "none",
    }}
  />
);

// Flash on cuts: at = scene-change frames (timeline.cuts)
export const Flash: React.FC<{ at: number[]; color?: string; strength?: number }> = ({
  at,
  color = "#fff",
  strength = 0.7,
}) => {
  const frame = useCurrentFrame();
  const opacity = Math.max(0, ...at.map((c) => interpolate(frame, [c - 1, c, c + 5], [0, strength, 0], clamp)));
  return <AbsoluteFill style={{ backgroundColor: color, opacity, pointerEvents: "none" }} />;
};

// Warm glow sweeping across the screen around cuts
export const LightLeak: React.FC<{ at: number[]; color?: string }> = ({ at, color = "255,170,90" }) => {
  const frame = useCurrentFrame();
  return (
    <>
      {at.map((c, i) => {
        const opacity = interpolate(frame, [c - 14, c, c + 18], [0, 0.85, 0], clamp);
        if (opacity === 0) {
          return null;
        }
        const x = interpolate(frame, [c - 14, c + 18], [-20, 120], clamp);
        return (
          <AbsoluteFill
            key={c}
            style={{
              mixBlendMode: "screen",
              opacity,
              pointerEvents: "none",
              background: `radial-gradient(circle at ${x}% ${i % 2 === 0 ? 30 : 70}%, rgba(${color},0.95) 0%, rgba(${color},0.35) 25%, transparent 55%)`,
            }}
          />
        );
      })}
    </>
  );
};

// Progress bar along the top edge, spanning the whole video
export const ProgressBar: React.FC<{ color: string; height?: number }> = ({ color, height = 6 }) => {
  const frame = useCurrentFrame();
  const { width, durationInFrames } = useVideoConfig();
  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        height,
        width: interpolate(frame, [0, durationInFrames - 1], [0, width], clamp),
        backgroundColor: color,
      }}
    />
  );
};

// Camera shake after an impact (hits = impact frames).
// Usage: const s = useShake([12]); style={{ transform: `translate(${s.x}px, ${s.y}px)` }}
export const useShake = (hits: number[], strength = 16) => {
  const frame = useCurrentFrame();
  const amp = hits.reduce((acc, h) => acc + interpolate(frame, [h, h + 1, h + 12], [0, strength, 0], clamp), 0);
  return {
    x: (random(`shake-x-${frame}`) - 0.5) * amp,
    y: (random(`shake-y-${frame}`) - 0.5) * amp,
  };
};
