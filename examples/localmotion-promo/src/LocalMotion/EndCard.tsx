import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { RevealLine, Words, clamp } from "../kit";
import { colors, gridBg, type } from "./theme";

// Scene 9 — END: wordmark, then the tagline
export const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const glow = 0.5 + 0.5 * Math.sin(frame / 24);
  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <div style={gridBg} />
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 300,
          height: 480,
          background: `radial-gradient(ellipse at center, rgba(62,224,127,${0.08 + glow * 0.08}), transparent 68%)`,
        }}
      />

      <div style={{ position: "absolute", left: 115, top: 330, right: 115 }}>
        <div style={{ ...type.display, fontSize: 220, lineHeight: 0.95, color: colors.paper }}>
          <Words text="localmotion" delay={8} stagger={2} />
        </div>
        <div style={{ width: interpolate(frame, [44, 62], [0, 420], clamp), height: 6, backgroundColor: colors.accent, margin: "46px 0 40px" }} />
        <div style={{ ...type.body, fontSize: 88, lineHeight: 1.12, color: colors.paper }}>
          <RevealLine delay={56}>Open source.</RevealLine>
          <RevealLine delay={66} style={{ color: colors.accent }}>
            Your GPU, your videos.
          </RevealLine>
        </div>
      </div>
    </AbsoluteFill>
  );
};
