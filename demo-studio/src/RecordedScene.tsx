import { Video } from "@remotion/media";
import { AbsoluteFill, Img, Sequence, staticFile, useCurrentFrame, useVideoConfig, delayRender, continueRender } from "remotion";
import { useEffect, useState } from "react";
import { base, palette } from "./style";
import { captions } from "./captions";

type Status = {
  time: number; secured: boolean; delivery_pending: boolean; fault: boolean;
  door: string; latch: string; parcel: string; link: string; pending: number;
  endpoint_ids: number[]; endpoint_duplicate_packets: number;
  door_angle_rad: number; latch_position_m: number;
  events: {id: number; time: number; kind: string; detail: string}[];
};
type Data = {
  chapters: {at: number; title: string; description: string}[];
  samples: {at: number; status: Status}[];
};

// Both camera views use the same simulation time. The interface movie is a
// browser capture of the real page; its buttons drove this recorded run.
const controlsAt = (mode: string, time: number) => {
  const intervals = mode === "workflow"
    ? [[0, 2.55], [4.65, 5.95], [7.8, 9.0], [11.9, 16.9], [19.5, 20.65], [23.0, 24.2]]
    : [[0, 25.1], [26.1, 29.0], [32.3, 35.8]];
  return intervals.some(([start, end]) => time >= start && time < end);
};

const Scene: React.FC<{mode: "workflow" | "resilience"; held?: boolean}> = ({mode, held = false}) => {
  const [handle] = useState(() => delayRender("Recorded telemetry"));
  const [data, setData] = useState<Data | null>(null);
  useEffect(() => {
    fetch(staticFile(`${mode}.json`)).then(r => r.json()).then(recording => {
      setData(recording); continueRender(handle);
    }).catch(error => { throw error; });
  }, [mode, handle]);
  const currentFrame = useCurrentFrame();
  const fps = useVideoConfig().fps;
  const rawTime = currentFrame / fps;
  const inspectAckClick = mode === "resilience" && !held && rawTime >= 20.9 && rawTime < 21.7;
  const time = held ? 7 : inspectAckClick ? 20.9 : rawTime;
  const paused = held || inspectAckClick;
  if (!data) return null;
  const status = (data.samples.findLast(row => row.at <= time) || data.samples[0]).status;
  const chapter = captions[mode].findLast(item => item.at <= time) || captions[mode][0];
  const controls = controlsAt(mode, time);
  const security = status.fault ? "Fault · unsecured" : status.secured ? "Secured" : "Not secured";
  const description = status.delivery_pending
    ? "Parcel detected. Delivery waits for the door to close and the bolt to lock."
    : chapter.description;
  const measurements = mode === "workflow"
    ? [["Door angle", `${Math.round(status.door_angle_rad * 180 / Math.PI)}°`], ["Bolt travel", `${Math.round(status.latch_position_m * 1000)} mm`], ["Parcel", status.parcel]]
    : [["Bolt travel", `${Math.round(status.latch_position_m * 1000)} mm`], ["Awaiting ACK", String(status.pending)], ["Unique receipts", String(status.endpoint_ids.length)]];
  return <AbsoluteFill style={base}>
    <div style={{height:60, padding:"12px 36px", display:"flex", justifyContent:"space-between", borderBottom:"1px solid #ccc", fontSize:27}}>
      <span>Parcel Guard / {controls ? "Live control interface" : "Webots simulation"}</span>
      <span style={{color:status.fault ? palette.red : palette.ink}}>{controls ? (mode === "workflow" ? "Delivery and retrieval" : (paused ? "Failure tests · paused for inspection" : "Failure tests")) : `${security} · ${status.time.toFixed(1)} s`}</span>
    </div>
    {controls
      ? (paused
        ? <Img src={staticFile(held ? "expired-code.png" : "drop-acks.png")} style={{position:"absolute", left:96, top:60, width:1728, height:900, objectFit:"contain"}} />
        : <Video src={staticFile(`${mode}-interface.mp4`)} muted style={{position:"absolute", left:96, top:60, width:1728, height:900}} objectFit="contain" />)
      : <>
          <Video src={staticFile(`${mode}.mp4`)} muted style={{position:"absolute", left:16, top:94, width:1450, height:816}} objectFit="contain" />
          <div style={{position:"absolute", left:1510, top:180, width:350}}>
            <div style={{fontSize:26, color:palette.muted, marginBottom:32}}>Measured feedback</div>
            {measurements.map(([label, value]) => <div key={label} style={{padding:"22px 0", borderTop:"1px solid #ccc"}}>
              <div style={{fontSize:28, color:palette.muted}}>{label}</div>
              <div style={{fontSize:46, marginTop:8, fontVariantNumeric:"tabular-nums"}}>{value}</div>
            </div>)}
          </div>
        </>}
    <div style={{position:"absolute", left:0, right:0, bottom:0, height:120, padding:"12px 36px", borderTop:"2px solid #333", background:"white"}}>
      <div style={{fontSize:30, fontWeight:600, marginBottom:6}}>{held ? "Expired code denied" : chapter.title}</div>
      <div style={{fontSize:34, lineHeight:1.2}}>{held ? "The controller rejects the expired courier code. The box remains locked." : description}</div>
    </div>
  </AbsoluteFill>;
};

export const RecordedScene: React.FC<{mode: "workflow" | "resilience"}> = ({mode}) => {
  const frame = useCurrentFrame();
  if (mode === "resilience" && frame >= 210) {
    if (frame < 270) return <Scene mode={mode} held />;
    return <Sequence from={60} layout="none"><Scene mode={mode} /></Sequence>;
  }
  return <Scene mode={mode} />;
};
