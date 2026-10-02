import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Counter, RevealLine, clamp, stagger } from "../kit";
import { colors, gridBg, type } from "./theme";

const ITEMS = [
  { label: "tokens", from: 128000, to: 0 },
  { label: "API bills", from: 9999, to: 0 },
  { label: "GPU", from: 0, to: 1 },
];

// Scene 7 — BIG NUMBERS: the counters land on 0 and stay stuck there
export const Numbers: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <div style={gridBg} />
      {/* soft green glow in the middle, breathing */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 340,
          height: 400,
          background: `radial-gradient(ellipse at center, rgba(62,224,127,${
            0.1 + 0.06 * Math.sin((frame / 45) * Math.PI * 2)
          }), transparent 65%)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 115,
          top: 270,
          ...type.detail,
          fontSize: 36,
          color: colors.dim,
          letterSpacing: "0.3em",
          opacity: interpolate(frame, [4, 14], [0, 1], clamp),
        }}
      >
        <RevealLine delay={4}>THE MATH</RevealLine>
      </div>

      <div style={{ position: "absolute", left: 115, right: 115, top: 430, display: "flex" }}>
        {ITEMS.map((item, i) => {
          const d = 6 + stagger(i, ITEMS.length, 14);
          const pop = spring({ frame: frame - d, fps, config: { damping: 12, stiffness: 130 } });
          return (
            <div key={item.label} style={{ flex: 1, textAlign: "center", opacity: frame >= d ? 1 : 0 }}>
              <div
                style={{
                  ...type.display,
                  fontSize: 230,
                  lineHeight: 0.95,
                  color: colors.accent,
                  transform: `scale(${0.8 + pop * 0.2})`,
                }}
              >
                <Counter
                  to={item.to}
                  from={item.from}
                  delay={d + 2}
                  duration={24}
                  format={(n) => Math.round(n).toLocaleString("en-US")}
                />
              </div>
              <div
                style={{
                  ...type.detail,
                  fontSize: 36,
                  letterSpacing: "0.28em",
                  color: colors.paper,
                  marginTop: 26,
                  opacity: interpolate(frame, [d + 14, d + 22], [0, 1], clamp),
                }}
              >
                {item.label.toUpperCase()}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
