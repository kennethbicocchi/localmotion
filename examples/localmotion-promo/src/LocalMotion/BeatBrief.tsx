import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { RevealLine, SafeBlock, Typewriter, clamp } from "../kit";
import { colors, gridBg, panel, type } from "./theme";

// Scene 3 — STEP 01: a brief being typed in a terminal
export const BeatBrief: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <div style={gridBg} />

      <SafeBlock at={250}>
        <div style={{ ...type.detail, fontSize: 38, color: colors.accent, letterSpacing: "0.25em" }}>
          <RevealLine delay={4}>STEP 01</RevealLine>
        </div>
        <div style={{ ...type.display, fontSize: 118, lineHeight: 1.0, color: colors.paper, marginTop: 18 }}>
          <RevealLine delay={10}>Write</RevealLine>
          <RevealLine delay={16}>a brief.</RevealLine>
        </div>
      </SafeBlock>

      {/* terminal window on the right */}
      <div
        style={{
          position: "absolute",
          left: 1080,
          top: 240,
          width: 760,
          height: 560,
          ...panel,
          boxShadow: "0 40px 120px rgba(0,0,0,0.6)",
          opacity: interpolate(frame, [8, 20], [0, 1], clamp),
          transform: `translateY(${interpolate(frame, [8, 20], [40, 0], clamp)}px)`,
        }}
      >
        {/* title bar */}
        <div style={{ position: "relative", height: 56, borderBottom: `1px solid ${colors.dim}` }}>
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              style={{
                position: "absolute",
                left: 20 + i * 26,
                top: 21,
                width: 14,
                height: 14,
                borderRadius: "50%",
                backgroundColor: i === 2 ? colors.accent : "#22303a",
              }}
            />
          ))}
          <div style={{ ...type.detail, fontSize: 32, color: colors.dim, position: "absolute", left: 130, top: 12 }}>
            brief.md
          </div>
        </div>
        {/* typed brief */}
        <div style={{ ...type.detail, fontSize: 33, lineHeight: 1.75, color: colors.paper, padding: "36px 40px", opacity: 0.95 }}>
          <div>
            <span style={{ color: colors.accent }}>&gt; </span>
            <Typewriter text="a 30-second racing-game trailer" delay={20} cps={46} />
          </div>
          <div>
            <span style={{ color: colors.accent }}>&gt; </span>
            <Typewriter text="fast cuts, neon, night city" delay={42} cps={46} />
          </div>
          <div>
            <span style={{ color: colors.accent }}>&gt; </span>
            <Typewriter text="output: vertical video" delay={64} cps={46} />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
