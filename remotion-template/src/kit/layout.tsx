import React from "react";
import { useVideoConfig } from "remotion";

// Margins that text and logos must stay inside. In 9:16 reels the Instagram/TikTok
// interface covers about 220 px at the top and 400 px at the bottom.
export const useSafe = () => {
  const { width, height } = useVideoConfig();
  const vertical = height > width;
  return vertical
    ? { top: 220, bottom: height - 400, left: 72, right: width - 72, width: width - 144 }
    : {
        top: Math.round(height * 0.07),
        bottom: Math.round(height * 0.93),
        left: Math.round(width * 0.06),
        right: Math.round(width * 0.94),
        width: Math.round(width * 0.88),
      };
};

// Text block positioned inside the safe area.
// at = distance in px from the top of the video (anchor "top") or from the bottom (anchor "bottom");
// it is pushed inside the safe area if needed.
export const SafeBlock: React.FC<{
  at: number;
  anchor?: "top" | "bottom";
  align?: "left" | "center";
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ at, anchor = "top", align = "left", children, style }) => {
  const safe = useSafe();
  const { height } = useVideoConfig();
  const pos =
    anchor === "top" ? { top: Math.max(safe.top, at) } : { bottom: Math.max(height - safe.bottom, at) };
  return (
    <div
      style={{
        position: "absolute",
        left: safe.left,
        width: safe.width,
        textAlign: align,
        ...pos,
        ...style,
      }}
    >
      {children}
    </div>
  );
};
