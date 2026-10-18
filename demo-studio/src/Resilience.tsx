import { Series } from "remotion";
import { Opening } from "./Opening";
import { RecordedScene } from "./RecordedScene";
import { Evidence } from "./Evidence";
export const Resilience = () => (
  <Series>
    <Series.Sequence durationInFrames={120} name="Opening">
      <Opening mode="resilience" />
    </Series.Sequence>
    <Series.Sequence
      durationInFrames={1203}
      name="Webots security and recovery"
    >
      <RecordedScene mode="resilience" />
    </Series.Sequence>
    <Series.Sequence durationInFrames={210} name="Verified evidence">
      <Evidence mode="resilience" />
    </Series.Sequence>
  </Series>
);
