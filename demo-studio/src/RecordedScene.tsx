import { Video } from "@remotion/media";
import {
  AbsoluteFill,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  delayRender,
  continueRender,
} from "remotion";
import { useEffect, useState } from "react";
import { base, palette } from "./style";

type Status = {
  time: number;
  phase: string;
  secured: boolean;
  delivery_pending: boolean;
  fault: boolean;
  door: string;
  latch: string;
  parcel: string;
  link: string;
  pending: number;
  endpoint_ids: number[];
  endpoint_duplicate_packets: number;
  door_angle_rad: number;
  latch_position_m: number;
  events: { id: number; time: number; kind: string; detail: string }[];
};
type Data = {
  chapters: { at: number; title: string; description: string }[];
  samples: { at: number; status: Status }[];
};

const readable = (value: string) => value.replaceAll("_", " ");

export const RecordedScene: React.FC<{ mode: "workflow" | "resilience" }> = ({
  mode,
}) => {
  const [handle] = useState(() => delayRender("Recorded telemetry"));
  const [data, setData] = useState<Data | null>(null);
  useEffect(() => {
    fetch(staticFile(`${mode}.json`))
      .then((r) => r.json())
      .then((recording) => {
        setData(recording);
        continueRender(handle);
      })
      .catch((error) => {
        throw error;
      });
  }, [mode, handle]);

  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const time = frame / fps;
  if (!data) return null;
  const status = (
    data.samples.findLast((row) => row.at <= time) || data.samples[0]
  ).status;
  const chapter =
    data.chapters.findLast((item) => item.at <= time) || data.chapters[0];
  const { title } = chapter;
  const description = status.delivery_pending
    ? "Delivery is pending until the door closes and the bolt locks."
    : chapter.description;
  const event = status.events
    .filter(
      (item) =>
        !["boot", "sensor_fault", "sensor_recovered"].includes(item.kind),
    )
    .at(-1);
  const security = status.fault
    ? "Fault: not secured"
    : status.secured
      ? "Secured"
      : "Not secured";

  return (
    <AbsoluteFill style={base}>
      <Video
        src={staticFile(`${mode}.mp4`)}
        muted
        style={{ position: "absolute", width: "100%", height: "100%" }}
        objectFit="contain"
      />
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 55,
          padding: "14px 30px",
          background: "#ffffffed",
          display: "flex",
          justifyContent: "space-between",
          fontSize: 23,
        }}
      >
        <span>
          Webots simulation /{" "}
          {mode === "workflow" ? "Delivery and retrieval" : "Failure tests"}
        </span>
        <span style={{ fontFamily: "monospace" }}>
          {status.time.toFixed(1)} s
        </span>
      </div>
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          background: "#fffffff5",
          borderTop: "1px solid #888",
          padding: "19px 34px 17px",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            justifyContent: "space-between",
            gap: 30,
            marginBottom: 9,
          }}
        >
          <strong style={{ fontSize: 28, fontWeight: 600 }}>{title}</strong>
          <span
            style={{
              fontSize: 24,
              color: status.fault ? palette.red : palette.ink,
            }}
          >
            {security}
          </span>
        </div>
        <div
          style={{
            fontSize: 30,
            lineHeight: 1.3,
            minHeight: 46,
            maxWidth: 1790,
          }}
        >
          {description}
        </div>
        <div
          style={{
            borderTop: "1px solid #ccc",
            paddingTop: 12,
            display: "flex",
            justifyContent: "space-between",
            gap: 20,
            fontSize: 23,
            fontFamily: "monospace",
            color: palette.muted,
          }}
        >
          <span>
            door {status.door_angle_rad.toFixed(2)} rad · bolt{" "}
            {Math.round(status.latch_position_m * 1000)} mm · parcel{" "}
            {status.parcel}
          </span>
          <span>
            link {status.link} · queued {status.pending} · received{" "}
            {status.endpoint_ids.length} · duplicates{" "}
            {status.endpoint_duplicate_packets}
          </span>
        </div>
        <div
          style={{
            fontFamily: "monospace",
            color: palette.muted,
            fontSize: 22,
            marginTop: 9,
          }}
        >
          {event
            ? `Event #${event.id}: ${readable(event.kind)}: ${event.detail}`
            : "Waiting for the first event."}
        </div>
      </div>
    </AbsoluteFill>
  );
};
