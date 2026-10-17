import {
  AbsoluteFill,
  staticFile,
  delayRender,
  continueRender,
} from "remotion";
import { useEffect, useState } from "react";
import { base, palette } from "./style";

type Summary = {
  presence: string;
  f1: string;
  falseAlarms: string;
  cycles: string;
  unauthorized: string;
  recovered: string;
};

export const Evidence: React.FC<{
  mode: "workflow" | "resilience" | "final";
}> = ({ mode }) => {
  const [handle] = useState(() => delayRender("Evaluation summary"));
  const [summary, setSummary] = useState<Summary | null>(null);
  useEffect(() => {
    fetch(staticFile("summary.json"))
      .then((r) => r.json())
      .then((data) => {
        setSummary(data);
        continueRender(handle);
      })
      .catch((error) => {
        throw error;
      });
  }, [handle]);
  if (!summary) return null;

  const handling = [
    ["Correct parcel-presence decisions", summary.presence],
    ["Event classification, 60 sequences", `${summary.f1} macro F1`],
    ["Completed opening and closing cycles", summary.cycles],
  ];
  const failures = [
    ["Unauthorized unlocks", summary.unauthorized],
    ["Offline alerts recovered", summary.recovered],
    ["False tamper alarms", summary.falseAlarms],
  ];
  const rows =
    mode === "workflow"
      ? handling
      : mode === "resilience"
        ? failures
        : [...handling, ...failures];

  return (
    <AbsoluteFill style={{ ...base, padding: "100px 180px" }}>
      <h1 style={{ fontSize: 46, fontWeight: 600, margin: "0 0 42px" }}>
        Test results
      </h1>
      <table
        style={{ width: "100%", borderCollapse: "collapse", fontSize: 31 }}
      >
        <thead>
          <tr style={{ borderBottom: "2px solid #444", textAlign: "left" }}>
            <th style={{ padding: "12px 0", fontWeight: 600 }}>Test</th>
            <th style={{ padding: "12px 0", fontWeight: 600, width: 350 }}>
              Result
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([label, value]) => (
            <tr key={label} style={{ borderBottom: "1px solid #ccc" }}>
              <td style={{ padding: "19px 0" }}>{label}</td>
              <td
                style={{
                  padding: "19px 0",
                  fontVariantNumeric: "tabular-nums",
                }}
              >
                {value}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p
        style={{
          fontSize: 27,
          color: palette.muted,
          lineHeight: 1.5,
          marginTop: 40,
        }}
      >
        Results from the scripted Webots trials.
        <br />
        Hardware strength and real networks need separate testing.
      </p>
      <div
        style={{
          position: "absolute",
          bottom: 55,
          fontSize: 23,
          color: palette.muted,
        }}
      >
        Trial details: results/REPORT.md
      </div>
    </AbsoluteFill>
  );
};
