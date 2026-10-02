import React from "react";
import { AbsoluteFill, Composition, Img, staticFile } from "remotion";
import { loadType } from "../kit";

const type = loadType("tech");
const c = { ink: "#0b0d12", paper: "#eef1f6", muted: "#8b93a5", accent: "#4ee0a8" };

const Card: React.FC<{ src: string; w: number; h: number; x: number; y: number; r: number }> = ({ src, w, h, x, y, r }) => (
  <div
    style={{
      position: "absolute", left: x, top: y, width: w, height: h, borderRadius: 18, overflow: "hidden",
      transform: `rotate(${r}deg)`, boxShadow: "0 30px 80px rgba(0,0,0,0.6), 0 0 0 2px rgba(255,255,255,0.08)",
    }}
  >
    <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", maxWidth: "none" }} />
  </div>
);

const Banner: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: c.ink }}>
    <AbsoluteFill
      style={{
        backgroundImage: "linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)",
        backgroundSize: "40px 40px",
      }}
    />
    <AbsoluteFill style={{ background: `radial-gradient(circle at 78% 50%, rgba(78,224,168,0.18), transparent 55%)` }} />
    <Card src="_banner/blockwise.png" w={430} h={242} x={700} y={330} r={4} />
    <Card src="_banner/keeper.png" w={190} h={338} x={1030} y={60} r={6} />
    <Card src="_banner/neon.png" w={200} h={356} x={760} y={40} r={-5} />
    <div style={{ position: "absolute", left: 70, top: 120, width: 640 }}>
      <div style={{ ...type.detail, fontSize: 22, color: c.accent, letterSpacing: "0.12em" }}>LOCAL MODEL · MOTION DESIGN</div>
      <div style={{ ...type.display, fontSize: 112, lineHeight: 0.95, color: c.paper, marginTop: 14 }}>localmotion</div>
      <div style={{ ...type.body, fontSize: 32, lineHeight: 1.25, color: c.paper, marginTop: 26 }}>
        Animated videos made by an open model on your own GPU.
      </div>
      <div style={{ ...type.display, fontSize: 40, color: c.accent, marginTop: 34 }}>0 tokens. 0 API bills.</div>
      <div style={{ ...type.detail, fontSize: 20, color: c.muted, marginTop: 40 }}>Qwen 3.8 27B · Remotion · LM Studio · one 24 GB GPU</div>
    </div>
  </AbsoluteFill>
);

export const RepoBanner: React.FC = () => (
  <Composition id="RepoBanner" component={Banner} durationInFrames={1} fps={30} width={1280} height={640} />
);
