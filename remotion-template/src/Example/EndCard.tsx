import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { RevealLine, SafeBlock, clamp } from "../kit";
import { colors, type } from "./theme";

// Layout D: typography only, no photo, a deliberate pause before the end
export const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const line = interpolate(frame, [20, 50], [0, 360], clamp);
  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <SafeBlock at={560}>
        <div style={{ ...type.body, fontSize: 170, lineHeight: 1.02, color: colors.paper }}>
          <RevealLine delay={4}>The light</RevealLine>
          <RevealLine delay={12}>never went</RevealLine>
          <RevealLine delay={20} style={{ color: colors.accent }}>
            out.
          </RevealLine>
        </div>
        <div style={{ width: line, height: 4, backgroundColor: colors.accent, margin: "48px 0 28px" }} />
        <div style={{ ...type.detail, fontSize: 40, color: colors.paper, opacity: interpolate(frame, [36, 50], [0, 0.8], clamp) }}>
          THE LAST KEEPER
        </div>
      </SafeBlock>
    </AbsoluteFill>
  );
};
