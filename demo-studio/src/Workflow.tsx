import { Series } from "remotion";
import { Opening } from "./Opening";
import { RecordedScene } from "./RecordedScene";
import { Evidence } from "./Evidence";
export const Workflow = () => (
  <Series>
    <Series.Sequence durationInFrames={120} name="Opening">
      <Opening mode="workflow" />
    </Series.Sequence>
    <Series.Sequence
      durationInFrames={855}
      name="Webots delivery and retrieval"
    >
      <RecordedScene mode="workflow" />
    </Series.Sequence>
    <Series.Sequence durationInFrames={210} name="Verified evidence">
      <Evidence mode="workflow" />
    </Series.Sequence>
  </Series>
);
