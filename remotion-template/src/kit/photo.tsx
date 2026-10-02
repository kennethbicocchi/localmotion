import React from "react";
import { Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, easeInOut } from "./time";

// A photo in public/. w and h are its real size, focus is the point to keep in frame,
// as percentages (x, y). The describe_media tool returns the right values.
export type PhotoInfo = {
  src: string;
  w: number;
  h: number;
  focus: [number, number];
};

export type Box = { left: number; top: number; width: number; height: number };

// "Cover" rectangle that centers the focus point in the box without ever leaving empty edges
export const coverOn = (photo: PhotoInfo, boxW: number, boxH: number, zoom = 1) => {
  const fx = (photo.focus[0] / 100) * photo.w;
  const fy = (photo.focus[1] / 100) * photo.h;
  const s = Math.max(boxW / photo.w, boxH / photo.h) * zoom;
  const width = photo.w * s;
  const height = photo.h * s;
  const left = Math.min(0, Math.max(boxW - width, boxW / 2 - fx * s));
  const top = Math.min(0, Math.max(boxH - height, boxH / 2 - fy * s));
  return { width, height, left, top, originX: fx * s, originY: fy * s };
};

// Photo with a slow camera move (Ken Burns) toward the focus point.
// The move lasts as long as the Sequence that contains it.
export const Photo: React.FC<{
  photo: PhotoInfo;
  box?: Box; // box in px; full screen if omitted
  zoom?: [number, number]; // zoom at scene start and end. [1, 1.08] = slow push-in
  crop?: number; // extra fixed zoom to tighten on a detail (1.3 = tighter)
  drift?: [number, number]; // horizontal offset in px at scene start and end
  filter?: string; // e.g. "grayscale(1) contrast(1.3)"
  radius?: number;
  fade?: { side: "top" | "bottom"; color: string }; // dissolve one edge into the background: no hard edges
  style?: React.CSSProperties; // box style (borders, shadows)
}> = ({ photo, box, zoom = [1, 1.08], crop = 1, drift = [0, 0], filter, radius = 0, fade, style }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();
  const b = box ?? { left: 0, top: 0, width, height };
  const len = Number.isFinite(durationInFrames) ? durationInFrames : 150;
  const t = interpolate(frame, [0, len], [0, 1], { ...clamp, easing: easeInOut });
  const r = coverOn(photo, b.width, b.height, crop);
  const scale = zoom[0] + (zoom[1] - zoom[0]) * t;
  const dx = drift[0] + (drift[1] - drift[0]) * t;
  return (
    <div
      style={{
        position: "absolute",
        left: b.left,
        top: b.top,
        width: b.width,
        height: b.height,
        overflow: "hidden",
        borderRadius: radius,
        ...style,
      }}
    >
      <Img
        src={staticFile(photo.src)}
        style={{
          position: "absolute",
          maxWidth: "none", // Tailwind sets max-width: 100% on img, which would squash the photo
          left: r.left,
          top: r.top,
          width: r.width,
          height: r.height,
          transform: `translateX(${dx}px) scale(${scale})`,
          transformOrigin: `${r.originX}px ${r.originY}px`,
          filter,
        }}
      />
      {fade ? (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: `linear-gradient(to ${fade.side}, transparent 50%, ${fade.color} 97%)`,
          }}
        />
      ) : null}
    </div>
  );
};
