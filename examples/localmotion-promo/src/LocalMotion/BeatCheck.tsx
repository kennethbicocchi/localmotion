import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Photo, RevealLine, SafeBlock, clamp, stagger } from "../kit";
import { colors, gridBg, photos, type } from "./theme";

const CELLS = [0, 1, 2, 3];

// Scene 5 — STEP 03: it checks its work and looks at every frame
export const BeatCheck: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scan = interpolate(frame, [14, 59], [0, 1], { ...clamp });
  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <div style={gridBg} />

      <SafeBlock at={250}>
        <div style={{ ...type.detail, fontSize: 38, color: colors.accent, letterSpacing: "0.25em" }}>
          <RevealLine delay={4}>STEP 03</RevealLine>
        </div>
        <div style={{ ...type.display, fontSize: 100, lineHeight: 1.02, color: colors.paper, marginTop: 18, maxWidth: 880 }}>
          <RevealLine delay={10}>It checks its</RevealLine>
          <RevealLine delay={16}>work and looks</RevealLine>
          <RevealLine delay={22}>at every frame.</RevealLine>
        </div>
        <div
          style={{
            ...type.detail,
            fontSize: 32,
            color: colors.accent,
            marginTop: 40,
            opacity: interpolate(frame, [68, 80], [0, 1], clamp),
          }}
        >
          frame 240/240 — ok
        </div>
      </SafeBlock>

      {/* 2x2 grid of real frames being reviewed */}
      <div style={{ position: "absolute", left: 1010, top: 210, width: 760, height: 640 }}>
        {CELLS.map((i) => {
          const col = i % 2;
          const row = Math.floor(i / 2);
          const appear = interpolate(frame, [8 + stagger(i, 4), 8 + stagger(i, 4) + 14], [0, 1], clamp);
          const at = 28 + stagger(i, 4, 24);
          const checked = frame >= at;
          const cp = checked ? spring({ frame: frame - at, fps, config: { damping: 9, stiffness: 200 } }) : 0;
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: col * 390,
                top: row * 326,
                width: 370,
                height: 306,
                borderRadius: 12,
                overflow: "hidden",
                border: `2px solid ${checked ? colors.accent : colors.dim}`,
                opacity: appear,
                transform: `translateY(${(1 - appear) * 30}px)`,
              }}
            >
              <CellPhoto index={i} />
              {checked ? (
                <div
                  style={{
                    position: "absolute",
                    right: 12,
                    top: 12,
                    width: 44,
                    height: 44,
                    borderRadius: "50%",
                    backgroundColor: colors.accent,
                    transform: `scale(${cp})`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <div
                    style={{
                      width: 20,
                      height: 11,
                      borderRight: "4px solid #06130b",
                      borderBottom: "4px solid #06130b",
                      transform: "rotate(45deg) translateY(-3px)",
                    }}
                  />
                </div>
              ) : null}
            </div>
          );
        })}
        {/* scan bar sweeping across the grid */}
        <div
          style={{
            position: "absolute",
            left: scan * 760,
            top: 0,
            bottom: 0,
            width: 4,
            backgroundColor: colors.accent,
            boxShadow: "0 0 30px rgba(62,224,127,0.9)",
            opacity: frame < 14 ? 0 : frame > 63 ? 0 : 1,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

// The four sample frames, one per cell (kept small: no upscaling blur)
const CellPhoto: React.FC<{ index: number }> = ({ index }) => {
  const cell = [photos.racingDuel, photos.racingHud, photos.sandboxNight, photos.lighthouseTitle][index];
  return <Photo photo={cell} box={{ left: 0, top: 0, width: 370, height: 306 }} zoom={[1, 1.06]} />;
};
