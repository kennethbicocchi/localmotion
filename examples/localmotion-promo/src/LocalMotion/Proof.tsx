import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Photo, RevealLine, clamp, easeInOut } from "../kit";
import { colors, gridBg, photos, type } from "./theme";

const bob = (frame: number, phase: number) => Math.sin(frame / 18 + phase) * 8;
const loop = (frame: number, len: number) => (frame % len) / len;

// A vertical device frame with a photo and a playing progress bar
const Phone: React.FC<{ photo: (typeof photos)[keyof typeof photos]; x: number; tilt: number; delay: number; phase: number; frame: number; fps: number }> = ({
  photo,
  x,
  tilt,
  delay,
  phase,
  frame,
  fps,
}) => {
  const p = spring({ frame: frame - delay, fps, config: { damping: 14, stiffness: 110 } });
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: 190,
        width: 380,
        height: 672,
        borderRadius: 40,
        backgroundColor: "#10161c",
        border: "9px solid #1d2731",
        boxShadow: "0 50px 120px rgba(0,0,0,0.6)",
        transform: `translateY(${(1 - p) * 200 + bob(frame, phase)}px) rotate(${tilt}deg)`,
        opacity: frame >= delay ? 1 : 0,
      }}
    >
      <div style={{ position: "absolute", inset: 0, borderRadius: 30, overflow: "hidden" }}>
        <Photo photo={photo} box={{ left: 0, top: 0, width: 362, height: 654 }} zoom={[1.04, 1]} />
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            bottom: 0,
            height: 6,
            backgroundColor: "rgba(255,255,255,0.25)",
          }}
        >
          <div style={{ height: 6, width: loop(frame + phase * 30, 90) * 362, backgroundColor: colors.accent }} />
        </div>
        {/* playing dot */}
        <div
          style={{
            position: "absolute",
            left: 14,
            bottom: 18,
            width: 12,
            height: 12,
            borderRadius: "50%",
            backgroundColor: colors.accent,
            opacity: 0.5 + 0.5 * Math.sin(frame / 5),
          }}
        />
      </div>
    </div>
  );
};

// A monitor frame with stand
const Monitor: React.FC<{ photo: (typeof photos)[keyof typeof photos]; delay: number; phase: number; frame: number; fps: number }> = ({
  photo,
  delay,
  phase,
  frame,
  fps,
}) => {
  const p = spring({ frame: frame - delay, fps, config: { damping: 14, stiffness: 110 } });
  return (
    <div
      style={{
        position: "absolute",
        left: 575,
        top: 205 + bob(frame, phase),
        width: 770,
        opacity: frame >= delay ? 1 : 0,
        transform: `translateY(${(1 - p) * 160}px)`,
      }}
    >
      <div
        style={{
          width: 770,
          height: 452,
          borderRadius: 16,
          backgroundColor: "#10161c",
          border: "10px solid #1d2731",
          boxShadow: "0 50px 120px rgba(0,0,0,0.6)",
          overflow: "hidden",
        }}
      >
        <Photo photo={photo} box={{ left: 0, top: 0, width: 750, height: 432 }} zoom={[1.05, 1]} />
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 6, backgroundColor: "rgba(255,255,255,0.25)" }}>
          <div style={{ height: 6, width: loop(frame + 40, 100) * 750, backgroundColor: colors.accent }} />
        </div>
      </div>
      {/* stand */}
      <div style={{ width: 64, height: 44, backgroundColor: "#1d2731", margin: "0 auto" }} />
      <div style={{ width: 260, height: 14, borderRadius: 7, backgroundColor: "#1d2731", margin: "0 auto" }} />
    </div>
  );
};

// Scene 8 — PROOF: the sample videos playing in floating device frames
export const Proof: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const caption = (delay: number) =>
    interpolate(frame, [delay, delay + 12], [0, 1], { ...clamp, easing: easeInOut });
  return (
    <AbsoluteFill style={{ backgroundColor: colors.ink }}>
      <div style={gridBg} />
      <div style={{ position: "absolute", left: 115, top: 104, ...type.detail, fontSize: 34, color: colors.accent, letterSpacing: "0.3em" }}>
        <RevealLine delay={4}>PROOF</RevealLine>
      </div>

      <Phone photo={photos.racingDuel} x={150} tilt={-4} delay={10} phase={0} frame={frame} fps={fps} />
      <Monitor photo={photos.sandboxNight} delay={18} phase={2.1} frame={frame} fps={fps} />
      <Phone photo={photos.lighthouseTitle} x={1390} tilt={4} delay={26} phase={4.2} frame={frame} fps={fps} />

      {/* captions under each device */}
      <div style={{ position: "absolute", left: 60, top: 918, width: 500, textAlign: "center", opacity: caption(70), ...type.body, fontSize: 42, color: colors.paper }}>
        a racing-game trailer
      </div>
      <div style={{ position: "absolute", left: 540, top: 800, width: 830, textAlign: "center", opacity: caption(82), ...type.body, fontSize: 42, color: colors.paper }}>
        a sandbox-game pitch
      </div>
      <div style={{ position: "absolute", left: 1360, top: 918, width: 500, textAlign: "center", opacity: caption(94), ...type.body, fontSize: 42, color: colors.paper }}>
        a lighthouse short film
      </div>
    </AbsoluteFill>
  );
};
