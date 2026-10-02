import React from "react";
import { AbsoluteFill, Audio, Composition, Sequence, interpolate, staticFile } from "remotion";
import { Flash, Grain, Scenes, makeTimeline } from "../kit";
import { BeatBrief } from "./BeatBrief";
import { BeatCheck } from "./BeatCheck";
import { BeatCode } from "./BeatCode";
import { BeatPhone } from "./BeatPhone";
import { Definition } from "./Definition";
import { EndCard } from "./EndCard";
import { Glitch } from "./Glitch";
import { Hook } from "./Hook";
import { Numbers } from "./Numbers";
import { Proof } from "./Proof";
import { colors } from "./theme";

const timeline = makeTimeline([
  { len: 110, Comp: Hook },
  { len: 145, Comp: Definition },
  { len: 115, Comp: BeatBrief },
  { len: 110, Comp: BeatCode },
  { len: 110, Comp: BeatCheck },
  { len: 125, Comp: BeatPhone },
  { len: 170, Comp: Numbers },
  { len: 290, Comp: Proof },
  { len: 175, Comp: EndCard },
]);

// Soundtrack: delayed 21 frames so its drop (19.0 s in the track) lands on BeatPhone (19.7 s),
// with a short fade-out because the video ends before the track's tail.
const MUSIC_DELAY = 21;
const Soundtrack: React.FC = () => (
  <Sequence from={MUSIC_DELAY}>
    <Audio
      src={staticFile("localmotion-promo/soundtrack.mp3")}
      volume={(f) =>
        interpolate(f, [timeline.duration - MUSIC_DELAY - 15, timeline.duration - MUSIC_DELAY], [1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      }
    />
  </Sequence>
);

const Video: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: colors.ink }}>
    <Scenes timeline={timeline} enter="punch" />
    <Glitch at={timeline.cuts} />
    <Flash at={timeline.cuts} color={colors.paper} strength={0.35} />
    <Grain opacity={0.3} />
    <Soundtrack />
  </AbsoluteFill>
);

export const LocalMotion: React.FC = () => (
  <Composition
    id="LocalMotion"
    component={Video}
    durationInFrames={timeline.duration}
    fps={30}
    width={1920}
    height={1080}
  />
);
