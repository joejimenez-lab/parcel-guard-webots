# Running Parcel Guard

## Requirements

- Webots R2025a and Python 3.10 or later.
- The simulation and Python test suite need no pip dependencies.
- Node.js 22+ is needed only for video editing and dashboard DOM tests. FFmpeg and ffprobe are needed for media checks and video production.
- Rebuilding the final paper uses Python's `reportlab` package. The editable paper is `docs/FINAL_REPORT.md`; its data template is `docs/report_source.md`.

Open `worlds/delivery_box.wbt`, select real-time speed, and open the Parcel Guard Robot Window. Start with the parcel outside. Courier code `2468` permits one delivery and expires after 300 simulated seconds. Owner code `1357` permits collection and expires after 86,400 seconds. The selected purpose must match the code.

## Reading the panel

`SECURED` requires valid readings, a closed door, a locked bolt, no active grant, and no fault. A delivery event confirms a sensor transition; the box may still be open. A moving bolt has reached neither endpoint. The queue count shows events awaiting acknowledgment, while the endpoint count shows unique receipts.

`New session` resets policy state and demo tokens. It does not move the parcel. Move the parcel outside first when preparing another delivery. Resetting the simulation also resets the scene. All expiry and cooldown periods use simulation time.

## Troubleshooting

| Symptom | Meaning and action |
|---|---|
| Courier request denied | Check purpose, occupancy, expiry, prior use and the event-log reason. Start a new session for a new demo token. |
| Entry paused | Five failed credential attempts occurred within 300 simulated seconds. Wait 60 simulated seconds. |
| Bolt fault | Target was not reached within two seconds. Release the bolt fixture and wait for measured recovery. |
| Door fault | Closure has not completed after three seconds. Release the door fixture. The bolt stays retracted while the door is open. |
| Sensor unavailable | Readings are missing or not stable. Access remains disabled. Initial startup requires three usable samples. |
| Queue stays nonzero | The link may be offline, ACKs may be deliberately dropped, or the fixture controller may have stopped. Check the Webots console. |
| Empty/blank Robot Window | Confirm the correct world is running and select Parcel Guard's Robot Window. The HTML preview is not connected to live hardware. |
| Python controller exits | Check Webots' Python command in Preferences. Run Python 3.10+. The `controller` module is supplied by Webots when it launches the process. |
| Runner cannot find Webots | Set `WEBOTS_BIN` to the simulator executable. |
| Portability problem | The included run was tested on macOS. Keep all project directories together; use the provided paths relative to the repository root. |

## Repeating checks

Run `python3 scripts/run_all.py` from the repository root. It stops on a failed gate and saves the error in the corresponding report/log. Do not run concurrent Webots evaluation and recording processes against the same results directory.

For UI regressions, run `npm ci` inside `demo-studio`, return to the root, then run `node tests/dashboard.cjs`. This tests DOM rendering and command construction with recorded status and injected faults. Browser layout review is separate from live Webots controller testing.

The renderer commands are in the root README. After rendering, run `python3 scripts/finalize_media.py`, then `python3 scripts/package_project.py`. The package builder rejects stale evaluation or recording hashes. Keep the final report and presentation alongside the demos when submitting.
