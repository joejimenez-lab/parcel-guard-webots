import { AbsoluteFill } from "remotion";
import { base, palette } from "./style";

export const Opening: React.FC<{
  mode: "workflow" | "resilience" | "final";
}> = ({ mode }) => {
  const subject = {
    final: "Delivery, retrieval, and failure tests",
    workflow: "Courier delivery and owner retrieval",
    resilience: "Access checks, offline alerts, and bolt faults",
  }[mode];

  return (
    <AbsoluteFill
      style={{ ...base, justifyContent: "center", padding: "0 180px" }}
    >
      <div style={{ fontSize: 28, color: palette.muted, marginBottom: 30 }}>
        CS 5650 · Fall 2026
      </div>
      <h1
        style={{ fontSize: 62, fontWeight: 600, lineHeight: 1.15, margin: 0 }}
      >
        Package Delivery Security Box
      </h1>
      <div style={{ fontSize: 36, marginTop: 24 }}>{subject}</div>
      <div
        style={{
          fontSize: 28,
          color: palette.muted,
          lineHeight: 1.6,
          marginTop: 70,
        }}
      >
        Joshua Guico, Joe Jimenez, and Brandon Lopez
        <br />
        Webots R2025a · Python controller
      </div>
    </AbsoluteFill>
  );
};
