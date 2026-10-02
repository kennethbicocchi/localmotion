import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { RevealLine, Words, clamp, ease } from "../kit";
import { colors, gridBg, type } from "./theme";

// A GPU chip: body, pins and looping pulse rings
const GpuChip: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - 10, fps, config: { damping: 14, stiffness: 140 } });
  const t = (frame % 60) / 60; // 2 s pulse loop
  const ring = (i: number) => {
    const rt = (t + i / 3) % 1;
    return {
      scale: 1 + rt * 0.9,
      opacity: (1 - rt) * 0.55,
    };
  };
  const glow = 0.5 + 0.5 * Math.sin(frame / 60 * Math.PI * 2 - Math.PI / 2);
  return (
    <div
      style={{
        position: "relative",
        width: 360,
        height: 360,
        transform: `scale(${p})`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {[0, 1, 2].map((i) => {
        const r = ring(i);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              width: 300,
              height: 300,
              borderRadius: "50%",
              border: `2px solid ${colors.accent}`,
              transform: `scale(${r.scale})`,
              opacity: r.opacity,
            }}
          />
        );
      })}
      {/* pins */}
      {["top", "bottom"].map((side) => (
        <div
          key={side}
          style={{
            position: "absolute",
            [side]: -26,
            left: 30,
            right: 30,
            display: "flex",
            justifyContent: "space-between",
          }}
        >
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} style={{ width: 10, height: 26, backgroundColor: colors.dim, opacity: 0.6 + glow * 0.4 }} />
          ))}
        </div>
      ))}
      {/* body */}
      <div
        style={{
          width: 280,
          height: 280,
          borderRadius: 20,
          backgroundColor: "#0d1319",
          border: `2px solid ${colors.dim}`,
          boxShadow: `0 0 ${30 + glow * 60}px rgba(62,224,127,${0.25 + glow * 0.4})`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 10,
        }}
      >
        <div style={{ ...type.detail, fontSize: 44, color: colors.accent, letterSpacing: "0.3em" }}>GPU</div>
        <div
          style={{
            width: 120,
            height: 120,
            borderRadius: 10,
            backgroundColor: "#111a21",
            border: `1px solid ${colors.dim}`,
            boxShadow: `inset 0 0 30px rgba(62,224,127,${0.15 + glow * 0.45})`,
          }}
        />
      </div>
    </div>
  );
};

// Scene 2 — DEFINITION: name + one sentence, GPU chip pulsing on the right
export const Definition: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <div style={gridBg} />
      <div
        style={{
          position: "absolute",
          left: 960 - 180,
          top: 170,
          opacity: interpolate(frame, [4, 18], [0, 1], { ...clamp, easing: ease }),
          transform: `scale(${interpolate(frame, [4, 18], [0.92, 1], { ...clamp, easing: ease })})`,
        }}
      >
        <GpuChip />
      </div>
      <div style={{ position: "absolute", left: 115, right: 115, top: 600, textAlign: "center" }}>
        <div style={{ ...type.display, fontSize: 120, lineHeight: 1 }}>
          <RevealLine delay={10}>
            <span style={{ color: colors.paper }}>localmotion</span>
            <span style={{ color: colors.accent }}>:</span>
          </RevealLine>
        </div>
        <div style={{ ...type.body, fontSize: 58, lineHeight: 1.2, color: colors.paper, marginTop: 26 }}>
          <Words
            text="Motion-design videos made by an open model"
            delay={20}
            stagger={2}
            accent={["open", "model"]}
            accentColor={colors.accent}
          />
          <Words
            text="on your own GPU."
            delay={32}
            stagger={2}
            style={{ marginTop: 4 }}
          />
        </div>
      </div>
    </AbsoluteFill>
  );
};
