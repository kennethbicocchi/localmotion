import React from "react";
import { AbsoluteFill, interpolate, random, useCurrentFrame } from "remotion";
import { clamp } from "../kit";
import { colors } from "./theme";

// Glitch slice bursts that fire on every cut: a few horizontal bars jitter and fade
export const Glitch: React.FC<{ at: number[] }> = ({ at }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {at.map((c) => {
        const inWin = frame >= c - 3 && frame <= c + 6;
        if (!inWin) {
          return null;
        }
        const o = interpolate(frame, [c - 3, c - 1, c + 4, c + 6], [0, 0.9, 0.9, 0], clamp);
        return (
          <React.Fragment key={c}>
            {[0, 1, 2, 3].map((i) => {
              const y = random(`glitch-y-${c}-${i}`) * 1080;
              const h = 4 + random(`glitch-h-${c}-${i}`) * 14;
              const x = (random(`glitch-x-${c}-${i}`) - 0.5) * 140;
              const w = 200 + random(`glitch-w-${c}-${i}`) * 800;
              return (
                <div
                  key={i}
                  style={{
                    position: "absolute",
                    left: random(`glitch-l-${c}-${i}`) * 1200,
                    top: y,
                    width: w,
                    height: h,
                    backgroundColor: i % 2 === 0 ? colors.accent : colors.paper,
                    opacity: o * 0.8,
                    transform: `translateX(${x}px)`,
                    mixBlendMode: "screen",
                  }}
                />
              );
            })}
          </React.Fragment>
        );
      })}
    </AbsoluteFill>
  );
};
