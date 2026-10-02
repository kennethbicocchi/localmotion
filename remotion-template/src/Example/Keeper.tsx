import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Photo, RevealLine, SafeBlock, clamp } from "../kit";
import { colors, photos, type } from "./theme";

const BOX = { left: 0, top: 0, width: 1080, height: 1250 };

// Layout B: photo in the top two thirds fading into the background, text block below
export const Keeper: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <Photo
        photo={photos.keeper}
        box={BOX}
        zoom={[1, 1.08]}
        drift={[30, -10]}
        fade={{ side: "bottom", color: colors.ink }}
      />
      <SafeBlock at={1150}>
        <div
          style={{
            ...type.detail,
            fontSize: 40,
            color: colors.accent,
            opacity: interpolate(frame, [10, 20], [0, 1], clamp),
          }}
        >
          CAPO NERO — FORTY YEARS
        </div>
        <div style={{ ...type.body, fontSize: 84, lineHeight: 1.08, color: colors.paper, marginTop: 18 }}>
          <RevealLine delay={18}>Forty years</RevealLine>
          <RevealLine delay={26}>on the same rock,</RevealLine>
          <RevealLine delay={34}>one light a night.</RevealLine>
        </div>
      </SafeBlock>
    </AbsoluteFill>
  );
};
