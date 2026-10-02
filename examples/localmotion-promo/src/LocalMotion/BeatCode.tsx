import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { RevealLine, SafeBlock, clamp, stagger } from "../kit";
import { colors, gridBg, panel, type } from "./theme";

const LINES: { indent: number; parts: [string, string][] }[] = [
  { indent: 0, parts: [["import ", colors.dim], ['{ makeScene } from "localmotion"', colors.paper]] },
  { indent: 0, parts: [["export const ", colors.accent], ["Trailer = () => (", colors.paper]] },
  { indent: 1, parts: [["<Scene ", colors.paper], ["len={90}", colors.accent], [" enter=\"punch\">", colors.paper]] },
  { indent: 2, parts: [["<Photo ", colors.paper], ["zoom={[1, 1.08]}", colors.accent], [" />", colors.paper]] },
  { indent: 2, parts: [["<Title ", colors.paper], ["text=\"DUEL\"", colors.accent], [" />", colors.paper]] },
  { indent: 1, parts: [["</Scene>", colors.paper]] },
  { indent: 0, parts: [[")", colors.paper]] },
];

// Scene 4 — STEP 02: the model writes the video as code
export const BeatCode: React.FC = () => {
  const frame = useCurrentFrame();
  const sweep = interpolate(frame, [42, 70], [0, 1], { ...clamp });
  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <div style={gridBg} />

      <SafeBlock at={250}>
        <div style={{ ...type.detail, fontSize: 38, color: colors.accent, letterSpacing: "0.25em" }}>
          <RevealLine delay={4}>STEP 02</RevealLine>
        </div>
        <div style={{ ...type.display, fontSize: 108, lineHeight: 1.0, color: colors.paper, marginTop: 18, maxWidth: 880 }}>
          <RevealLine delay={10}>The model</RevealLine>
          <RevealLine delay={16}>writes the video</RevealLine>
          <RevealLine delay={22}>as code.</RevealLine>
        </div>
      </SafeBlock>

      {/* code editor on the right */}
      <div
        style={{
          position: "absolute",
          left: 1050,
          top: 220,
          width: 790,
          ...panel,
          boxShadow: "0 40px 120px rgba(0,0,0,0.6)",
          opacity: interpolate(frame, [8, 20], [0, 1], clamp),
          transform: `translateY(${interpolate(frame, [8, 20], [40, 0], clamp)}px)`,
        }}
      >
        <div style={{ position: "relative", height: 52, borderBottom: `1px solid ${colors.dim}` }}>
          <div style={{ ...type.detail, fontSize: 32, color: colors.dim, position: "absolute", left: 24, top: 12 }}>
            trailer.tsx — generated
          </div>
        </div>
        <div style={{ padding: "30px 34px", display: "flex", flexDirection: "column", gap: 14 }}>
          {LINES.map((line, i) => {
            const p = interpolate(frame, [22 + stagger(i, LINES.length), 22 + stagger(i, LINES.length) + 12], [0, 1], {
              ...clamp,
            });
            return (
              <div
                key={i}
                style={{
                  marginLeft: line.indent * 44,
                  overflow: "hidden",
                  width: p * 100,
                  opacity: p,
                  ...type.detail,
                  fontSize: 32,
                  whiteSpace: "nowrap",
                }}
              >
                {line.parts.map((part, j) => (
                  <span key={j} style={{ color: part[1] }}>
                    {part[0]}
                  </span>
                ))}
              </div>
            );
          })}
        </div>
        {/* footer: the token counter stays stuck at 0 */}
        <div
          style={{
            borderTop: `1px solid ${colors.dim}`,
            padding: "16px 34px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            opacity: interpolate(frame, [70, 80], [0, 1], clamp),
            transform: `translateY(${interpolate(frame, [70, 80], [16, 0], clamp)}px)`,
          }}
        >
          <div style={{ ...type.detail, fontSize: 32, color: colors.dim }}>tokens used</div>
          <div style={{ ...type.detail, fontSize: 34, color: colors.accent, fontWeight: 700 }}>0</div>
        </div>
      </div>

      {/* playhead sweep across the bottom: the code becomes a playing video */}
      <div style={{ position: "absolute", left: 1050, top: 840, width: 790, opacity: frame < 42 ? 0 : 1 }}>
        <div style={{ height: 8, borderRadius: 4, backgroundColor: "#16202a" }}>
          <div style={{ height: 8, borderRadius: 4, width: sweep * 790, backgroundColor: colors.accent }} />
        </div>
        <div style={{ ...type.detail, fontSize: 32, color: colors.dim, marginTop: 12 }}>preview — playing</div>
      </div>
    </AbsoluteFill>
  );
};
