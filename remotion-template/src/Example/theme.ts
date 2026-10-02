import { loadType, type PhotoInfo } from "../kit";

// One font pair, one background, one text color, ONE accent
export const type = loadType("documentary");

export const colors = {
  ink: "#0a0d10",
  paper: "#efe9df",
  accent: "#f2a33a", // lamp amber: used for one word or one line per scene, never more
};

// Copied as-is from describe_media("example")
export const photos = {
  lighthouse: { src: "example/lighthouse.jpg", w: 768, h: 1344, focus: [38, 27] },
  keeper: { src: "example/keeper.jpg", w: 768, h: 1344, focus: [62, 38] },
  logbook: { src: "example/logbook.jpg", w: 768, h: 1344, focus: [60, 50] },
} satisfies Record<string, PhotoInfo>;
