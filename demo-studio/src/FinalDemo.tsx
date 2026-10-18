import { AbsoluteFill, Series } from "remotion";
import { Opening } from "./Opening";
import { RecordedScene } from "./RecordedScene";
import { Evidence } from "./Evidence";
import { base, palette } from "./style";

const Transition = () => (
  <AbsoluteFill
    style={{ ...base, justifyContent: "center", padding: "0 180px" }}
  >
    <div style={{ fontSize: 48, fontWeight: 600 }}>Failure tests</div>
    <div style={{ fontSize: 32, color: palette.muted, marginTop: 24 }}>
      Invalid codes, offline alerts, and recovery from a blocked bolt.
    </div>
  </AbsoluteFill>
);

export const FinalDemo = () => (
  <Series>
    <Series.Sequence durationInFrames={120}>
      <Opening mode="final" />
    </Series.Sequence>
    <Series.Sequence durationInFrames={855}>
      <RecordedScene mode="workflow" />
    </Series.Sequence>
    <Series.Sequence durationInFrames={60}>
      <Transition />
    </Series.Sequence>
    <Series.Sequence durationInFrames={1203}>
      <RecordedScene mode="resilience" />
    </Series.Sequence>
    <Series.Sequence durationInFrames={270}>
      <Evidence mode="final" />
    </Series.Sequence>
  </Series>
);
