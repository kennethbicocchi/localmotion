import type React from "react";
import { loadFont as loadAnton } from "@remotion/google-fonts/Anton";
import { loadFont as loadBebas } from "@remotion/google-fonts/BebasNeue";
import { loadFont as loadDMSans } from "@remotion/google-fonts/DMSans";
import { loadFont as loadFraunces } from "@remotion/google-fonts/Fraunces";
import { loadFont as loadGeist } from "@remotion/google-fonts/Geist";
import { loadFont as loadInstrument } from "@remotion/google-fonts/InstrumentSerif";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadJetBrains } from "@remotion/google-fonts/JetBrainsMono";
import { loadFont as loadManrope } from "@remotion/google-fonts/Manrope";
import { loadFont as loadPlayfair } from "@remotion/google-fonts/PlayfairDisplay";
import { loadFont as loadSpaceMono } from "@remotion/google-fonts/SpaceMono";

// Three typographic roles, always the same:
// display = big titles, body = sentences, detail = labels, numbers, dates
export type Type = {
  display: React.CSSProperties;
  body: React.CSSProperties;
  detail: React.CSSProperties;
};

const L = { subsets: ["latin"] as ["latin"] };

// Proven font pairs. Pick ONE pair per video and never mix them.
export const FONT_PAIRS = {
  // Documentary, portrait, history: huge condensed titles + elegant italic
  documentary: (): Type => ({
    display: { fontFamily: loadAnton("normal", { weights: ["400"], ...L }).fontFamily, fontWeight: 400 },
    body: {
      fontFamily: loadPlayfair("italic", { weights: ["400"], ...L }).fontFamily,
      fontStyle: "italic",
      fontWeight: 400,
    },
    detail: {
      fontFamily: loadSpaceMono("normal", { weights: ["700"], ...L }).fontFamily,
      fontWeight: 700,
      textTransform: "uppercase",
      letterSpacing: "0.12em",
    },
  }),
  // Apps, software, technology: clean geometric sans + monospace
  tech: (): Type => {
    const geist = loadGeist("normal", { weights: ["500", "700", "800"], ...L }).fontFamily;
    return {
      display: { fontFamily: geist, fontWeight: 800, letterSpacing: "-0.03em" },
      body: { fontFamily: geist, fontWeight: 500, letterSpacing: "-0.01em" },
      detail: { fontFamily: loadJetBrains("normal", { weights: ["500"], ...L }).fontFamily, fontWeight: 500 },
    };
  },
  // Magazine, fashion, culture: cover serif + neutral sans
  editorial: (): Type => {
    const inter = loadInter("normal", { weights: ["400", "600"], ...L }).fontFamily;
    return {
      display: { fontFamily: loadInstrument("normal", { weights: ["400"], ...L }).fontFamily, fontWeight: 400 },
      body: { fontFamily: inter, fontWeight: 400 },
      detail: { fontFamily: inter, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.18em" },
    };
  },
  // Sports, events, punchy promos: condensed caps + grotesk
  impact: (): Type => ({
    display: { fontFamily: loadBebas("normal", { weights: ["400"], ...L }).fontFamily, fontWeight: 400 },
    body: { fontFamily: loadDMSans("normal", { weights: ["500", "700"], ...L }).fontFamily, fontWeight: 500 },
    detail: {
      fontFamily: loadSpaceMono("normal", { weights: ["700"], ...L }).fontFamily,
      fontWeight: 700,
      textTransform: "uppercase",
    },
  }),
  // Luxury, food, weddings, nature: soft serif + airy sans
  elegant: (): Type => {
    const manrope = loadManrope("normal", { weights: ["400", "600"], ...L }).fontFamily;
    return {
      display: { fontFamily: loadFraunces("normal", { weights: ["300"], ...L }).fontFamily, fontWeight: 300 },
      body: { fontFamily: manrope, fontWeight: 400 },
      detail: { fontFamily: manrope, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.22em" },
    };
  },
};

export type FontPair = keyof typeof FONT_PAIRS;

// Call ONCE, at the top of theme.ts: export const type = loadType("documentary");
export const loadType = (pair: FontPair): Type => FONT_PAIRS[pair]();
