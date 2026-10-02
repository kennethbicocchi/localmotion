import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { RevealLine, SafeBlock, Typewriter, clamp } from "../kit";
import { colors, gridBg, type } from "./theme";

// Scene 1 — HOOK: a terminal prompt types, then the question punches in.
export const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <div style={gridBg} />

      {/* terminal prompt, top-left of the safe area */}
      <div style={{ position: "absolute", left: 115, top: 200, display: "flex", alignItems: "flex-end" }}>
        <div style={{ ...type.detail, fontSize: 40, color: colors.dim }}>localmotion@gpu:~$&nbsp;</div>
        <div style={{ ...type.detail, fontSize: 40, color: colors.accent }}>
          <Typewriter text="what if your videos cost 0 tokens?" delay={2} cps={32} />
        </div>
      </div>

      <SafeBlock at={360}>
        <div style={{ ...type.display, fontSize: 150, lineHeight: 0.98, color: colors.paper }}>
          <RevealLine delay={12}>What if your</RevealLine>
          <RevealLine delay={20}>videos cost</RevealLine>
          <RevealLine delay={28} style={{ color: colors.accent }}>
            0 tokens?
          </RevealLine>
        </div>
      </SafeBlock>

      {/* glitch slices that fire mid-scene */}
      {[0, 1, 2].map((i) => {
        const y = 520 + i * 130;
        const x = interpolate(frame, [34, 37, 40], [-90, 60, 0], { ...clamp });
        const o = interpolate(frame, [34, 36, 42, 46], [0, 0.9, 0.9, 0], clamp);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: 115 + (i % 2) * 300,
              top: y,
              width: 700 - i * 160,
              height: 6 + i * 4,
              backgroundColor: i === 1 ? colors.accent : colors.paper,
              opacity: o,
              transform: `translateX(${x}px)`,
              mixBlendMode: "screen",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
