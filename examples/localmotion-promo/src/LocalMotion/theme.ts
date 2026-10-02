import type React from "react";
import { loadType, type PhotoInfo } from "../kit";

// Tech pair: geometric sans display + JetBrains Mono details
export const type = loadType("tech");

export const colors = {
  ink: "#070b0e", // deep tech black with a hint of teal
  paper: "#e9f1f2", // cool near-white
  accent: "#3ee07f", // terminal green: one word or one line per scene
  dim: "#3c4a52", // panel borders, secondary lines
};

// Copied as-is from describe_media("localmotion-promo")
export const photos = {
  racingDuel: { src: "localmotion-promo/racing-trailer-duel.png", w: 540, h: 960, focus: [50, 50] },
  racingHud: { src: "localmotion-promo/racing-trailer-hud.png", w: 540, h: 960, focus: [50, 95] },
  sandboxNight: { src: "localmotion-promo/sandbox-pitch-night.png", w: 960, h: 540, focus: [50, 50] },
  lighthouseTitle: { src: "localmotion-promo/lighthouse-film-title.png", w: 270, h: 480, focus: [48, 38] },
} satisfies Record<string, PhotoInfo>;

// Shared little helpers
export const panel: React.CSSProperties = {
  backgroundColor: "#0d1319",
  border: `1px solid ${colors.dim}`,
  borderRadius: 14,
};

export const dots = (i: number): React.CSSProperties => ({
  position: "absolute",
  width: 14,
  height: 14,
  borderRadius: "50%",
  backgroundColor: i === 2 ? colors.accent : "#22303a",
});

// Faint blueprint dot grid, for typography-only scenes
export const gridBg: React.CSSProperties = {
  position: "absolute",
  inset: 0,
  backgroundImage: `radial-gradient(${colors.dim}66 1.5px, transparent 1.5px)`,
  backgroundSize: "80px 80px",
  maskImage: "radial-gradient(ellipse at center, black 30%, transparent 78%)",
};
