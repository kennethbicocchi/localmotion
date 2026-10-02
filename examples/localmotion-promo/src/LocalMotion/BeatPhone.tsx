import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Photo, RevealLine, SafeBlock, clamp } from "../kit";
import { colors, gridBg, photos, type } from "./theme";

// Scene 6 — STEP 04: the finished video lands on your phone
export const BeatPhone: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const phone = spring({ frame: frame - 2, fps, config: { damping: 16, stiffness: 160 } });
  const bubble = spring({ frame: frame - 10, fps, config: { damping: 13, stiffness: 170 } });
  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <div style={gridBg} />

      <SafeBlock at={250}>
        <div style={{ ...type.detail, fontSize: 38, color: colors.accent, letterSpacing: "0.25em" }}>
          <RevealLine delay={2}>STEP 04</RevealLine>
        </div>
        <div
          style={{
            ...type.detail,
            fontSize: 34,
            color: colors.dim,
            marginTop: 34,
            opacity: interpolate(frame, [14, 26], [0, 1], clamp),
          }}
        >
          delivery: zero tokens, zero cloud
        </div>
        <div style={{ ...type.display, fontSize: 108, lineHeight: 1.02, color: colors.paper, marginTop: 26, maxWidth: 880 }}>
          <RevealLine delay={6}>The finished</RevealLine>
          <RevealLine delay={11}>video lands on</RevealLine>
          <RevealLine delay={16}>your phone.</RevealLine>
        </div>
      </SafeBlock>

      {/* phone frame on the right */}
      <div
        style={{
          position: "absolute",
          left: 1160,
          top: 140,
          width: 500,
          height: 800,
          borderRadius: 44,
          backgroundColor: "#10161c",
          border: "10px solid #1d2731",
          boxShadow: `0 60px 140px rgba(0,0,0,0.65), 0 0 0 2px ${colors.dim}55, 0 0 120px rgba(62,224,127,0.12)`,
          transform: `translateY(${(1 - phone) * 160}px) scale(${0.94 + phone * 0.06})`,
          overflow: "hidden",
        }}
      >
        {/* punch-hole camera */}
        <div style={{ position: "absolute", left: 232, top: 26, width: 36, height: 36, borderRadius: "50%", backgroundColor: "#05070a" }} />
        {/* status hint */}
        <div style={{ position: "absolute", left: 40, top: 34, ...type.detail, fontSize: 32, color: "#5b6a75" }}>9:41</div>

        {/* the generated video, playing full-screen */}
        <Photo photo={photos.racingHud} box={{ left: 0, top: 0, width: 480, height: 780 }} zoom={[1.16, 1.02]} />

        {/* bottom scrim + progress bar */}
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            bottom: 0,
            height: 220,
            background: "linear-gradient(transparent, rgba(0,0,0,0.78))",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 26,
            right: 26,
            bottom: 46,
            display: "flex",
            alignItems: "center",
            gap: 14,
          }}
        >
          <div style={{ flex: 1, height: 5, borderRadius: 3, backgroundColor: "rgba(255,255,255,0.25)", overflow: "hidden" }}>
            <div
              style={{
                height: 5,
                borderRadius: 3,
                backgroundColor: colors.accent,
                width: `${interpolate(frame, [8, 50], [12, 84], clamp)}%`,
              }}
            />
          </div>
          <div style={{ ...type.detail, fontSize: 32, color: colors.paper }}>0:30</div>
        </div>

        {/* chat notification sliding in over the video */}
        <div style={{ position: "absolute", left: 26, right: 26, bottom: 90, opacity: bubble }}>
          <div
            style={{
              backgroundColor: "#18222b",
              borderRadius: 24,
              borderTopLeftRadius: 8,
              padding: "16px 20px",
              transform: `translateY(${(1 - bubble) * 120}px)`,
              display: "flex",
              alignItems: "center",
              gap: 16,
            }}
          >
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: "50%",
                backgroundColor: colors.accent,
                flexShrink: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {/* play triangle: generic, no app logo */}
              <div
                style={{
                  width: 0,
                  height: 0,
                  borderTop: "10px solid transparent",
                  borderBottom: "10px solid transparent",
                  borderLeft: "15px solid #06130b",
                  marginLeft: 3,
                }}
              />
            </div>
            <div>
              <div style={{ ...type.body, fontSize: 32, fontWeight: 700, color: colors.paper }}>Your video is ready</div>
              <div style={{ ...type.detail, fontSize: 30, color: "#6b7d8a", marginTop: 4 }}>localmotion</div>
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
