import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Photo, RevealLine, SafeBlock, Scrim, clamp } from "../kit";
import { colors, photos, type } from "./theme";

// Layout A: full-bleed photo, huge title anchored low, kicker above it
export const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <Photo photo={photos.lighthouse} zoom={[1.18, 1.04]} filter="contrast(1.1) saturate(0.9)" />
      <Scrim side="bottom" size={1100} color={colors.ink} />
      <SafeBlock at={1010}>
        <div
          style={{
            ...type.detail,
            fontSize: 44,
            color: colors.accent,
            letterSpacing: interpolate(frame, [4, 40], [24, 12], clamp),
            opacity: interpolate(frame, [4, 14], [0, 1], clamp),
          }}
        >
          A SHORT FILM
        </div>
        <div style={{ ...type.display, fontSize: 250, lineHeight: 0.9, color: colors.paper, marginTop: 12 }}>
          <RevealLine delay={8}>THE LAST</RevealLine>
          <RevealLine delay={15}>KEEPER</RevealLine>
        </div>
      </SafeBlock>
    </AbsoluteFill>
  );
};
