import React from "react";
import { AbsoluteFill, Composition } from "remotion";
import { Flash, Grain, LightLeak, ProgressBar, Scenes, Vignette, makeTimeline } from "../kit";
import { EndCard } from "./EndCard";
import { Hook } from "./Hook";
import { Keeper } from "./Keeper";
import { Logbook } from "./Logbook";
import { colors } from "./theme";

// Scene lengths in frames (30 fps). Different on purpose: the rhythm breathes.
const timeline = makeTimeline([
  { len: 100, Comp: Hook },
  { len: 150, Comp: Keeper },
  { len: 130, Comp: Logbook },
  { len: 110, Comp: EndCard },
]);

const Video: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: colors.ink }}>
    <Scenes timeline={timeline} enter="punch" />
    <LightLeak at={timeline.cuts} />
    <Flash at={timeline.cuts} color={colors.paper} strength={0.5} />
    <Vignette strength={0.5} />
    <Grain opacity={0.3} />
    <ProgressBar color={colors.accent} />
  </AbsoluteFill>
);

export const Example: React.FC = () => (
  <Composition
    id="Example"
    component={Video}
    durationInFrames={timeline.duration}
    fps={30}
    width={1080}
    height={1920}
  />
);
