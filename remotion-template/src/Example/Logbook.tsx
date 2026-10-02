import React from "react";
import { AbsoluteFill } from "remotion";
import { Counter, Photo, RevealLine, SafeBlock, Scrim } from "../kit";
import { colors, photos, type } from "./theme";

// Layout C: dark full-bleed photo as texture, a giant number is the subject
export const Logbook: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <Photo photo={photos.logbook} zoom={[1.25, 1.12]} filter="brightness(0.55) saturate(0.8)" />
      <Scrim side="top" size={1000} color={colors.ink} />
      <SafeBlock at={300}>
        <Counter
          to={14610}
          delay={6}
          duration={50}
          style={{ ...type.display, fontSize: 260, lineHeight: 1, color: colors.accent }}
        />
        <div style={{ ...type.display, fontSize: 96, lineHeight: 1, color: colors.paper, marginTop: 10 }}>
          <RevealLine delay={30}>NIGHTS, ONE PAGE</RevealLine>
          <RevealLine delay={37}>EACH, IN THE LOGBOOK</RevealLine>
        </div>
      </SafeBlock>
    </AbsoluteFill>
  );
};
