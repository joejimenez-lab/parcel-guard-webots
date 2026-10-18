# Package Delivery Security Box

[![Delivery workflow](output/Parcel%20Guard%20Workflow%20Poster.jpg)](https://github.com/joejimenez-lab/parcel-guard-webots/releases/latest)

[Watch the demos](#demo-videos) · [Download the complete project](https://github.com/joejimenez-lab/parcel-guard-webots/releases/latest) · [Evaluation report](results/REPORT.md) · [Design](DESIGN.md)

Parcel Guard is the Webots simulation for our CS 5650 package delivery security box project. A Python controller reads 25 distance sensors, door and bolt positions, and motion. It checks access, recognizes parcel events, and retains alerts during simulated link outages.

## Submission files

- [What to upload and how to prepare for class](SUBMISSION.md)
- [Final report PDF](output/pdf/Parcel%20Guard%20-%20Final%20Report.pdf) and [editable LaTeX source](docs/parcel_guard_report.tex)
- [Final presentation](output/submission/Parcel%20Guard%20-%20Final%20Presentation.pptx), [PDF copy](output/pdf/Parcel%20Guard%20-%20Final%20Presentation.pdf), and [speaker guide](docs/PRESENTATION_GUIDE.md)
- [Rubric and proposal coverage](REQUIREMENTS.md), [user guide](docs/USER_GUIDE.md), and [test results](results/REPORT.md)
- [Complete project ZIP](https://github.com/joejimenez-lab/parcel-guard-webots/releases/latest), including the final walkthrough, two class clips, and raw recordings

The CS 5650 team is Joshua Guico, Joe Jimenez, and Brandon Lopez. The proposal assigns the team roles and suggests a 13-minute presentation plus two minutes for questions.

## Start here

1. Install **Webots R2025a** and **Python 3.10+**. The simulation uses the Python standard library and the controller API bundled with Webots; no pip packages are required.
2. Open **`worlds/delivery_box.wbt`** in Webots. Select real-time simulation speed, then run.
3. Open the **Parcel Guard Robot Window** from the robot's context menu / Robot Window control.
4. Select **Courier**, enter **2468**, and click **Unlock**. Wait for the door to open and bolt to retract. In **Test controls**, click **Place parcel** and wait for parcel detection. Click **Close and secure**, then wait for `SECURED` and the delivery event.
5. Select **Owner**, enter **1357**, and unlock. Wait for the open door, click **Remove parcel**, and wait for the retrieval event. Click **Close and secure**.

The courier code is single-use and expires 300 simulated seconds after issuance. The owner code is also single-use and expires after 86,400 simulated seconds. **New session** reissues demo tokens and resets policy state; move the parcel out first for another courier delivery. The clock uses simulated time, so fast mode also advances code expiry quickly.

### Fault and outage walkthrough

- Click **Disconnect link**, then **Impact** (space repeated impacts by >1 simulated second). Watch the queue grow. **Restore link** drains it only after endpoint ACKs.
- **Drop 3 ACKs** makes the endpoint receive retry packets while preserving unique event IDs.
- Start a **New session** if the owner token was already used. Unlock as owner and wait for the door to open fully. Click **Block bolt**, then **Close and secure**. The door closes, the bolt remains retracted, and a fault appears after two seconds. **Release bolt** removes the brake and restores force; measured feedback must reach locked before the box reports secured.
- Try the wrong role for a valid code, a used courier code, or five incorrect entries. The log explains each denial; five wrong codes in five simulated minutes pause entry for one minute.

## Demo videos

- [**Final Demonstration**](output/Parcel%20Guard%20-%20Final%20Demonstration.mp4) — 84-second complete walkthrough with captions and no narration.

- [**Delivery Workflow**](output/Parcel%20Guard%20-%20Delivery%20Workflow.mp4) — 40-second courier delivery, used-code rejection, and owner retrieval.
- [**Security Recovery**](output/Parcel%20Guard%20-%20Security%20Recovery.mp4) — 51-second access failures, offline alerts, lost-ACK retries, bolt fault, and recovery.
- **`output/index.html`** — local video gallery with evaluation results.
- **`output/raw/`** in the [complete release package](https://github.com/joejimenez-lab/parcel-guard-webots/releases/latest) — unedited native Webots footage. Recorded telemetry and scenario assertions are in `results/workflow_recording.json` and `results/resilience_recording.json`.

The videos alternate between native Webots footage and the actual control page. Code entries and test buttons drive the running Python controller; status and events come back from its device readings. Captions identify fixture movement and fault injection. Both camera views follow the same simulation clock.

## Evaluation

From the project root:

```sh
python3 scripts/run_all.py
```

On macOS the runner finds `/Applications/Webots.app/Contents/MacOS/webots`. Elsewhere set `WEBOTS_BIN` to the executable. Webots supplies the `controller` Python module when it starts each controller. If needed, set Webots' Python command in Preferences to a Python 3.10+ interpreter.

The command regenerates worlds, freezes source/configuration hashes, runs development and final simulator scenarios, verifies all gates, and exports the report and CSVs. It exits nonzero if a gate fails. The simulation environment used for the included results is Webots R2025a on macOS.

| Final requirement | Result |
|---|---:|
| Parcel presence | 50/50, balanced empty/occupied, noise and edge placements |
| Four-class event recognition | Macro F1 1.00 across 60 balanced sequences |
| Non-tamper false alarms | 0/45 |
| Measured motion-only baseline | Macro F1 0.10 |
| Normal motor cycles | 100/100 |
| Sensor-sample-to-local-queue latency | 30/30 within 1 simulated second |
| Offline alerts recovered exactly once | 100/100 across 10 outages |
| Mixed access attacks | 0 unauthorized unlocks in 30 attempts |
| Blocked bolt | Lock and unlock faults detected; measured recovery |
| Added failure cases | Obstructed door, expired grant, early close, malformed input |
| Policy and dashboard regressions | 38 policy checks and 14 DOM checks |

Read **`results/REPORT.md`** for denominators, timing definitions, seeds, confusion matrices, and limitations. **`results/evaluation_manifest.json`** links each result to source and configuration hashes. **`REQUIREMENTS.md`** maps proposal requirements to implementations and evidence.

## Code and design

```text
config/evaluation.json                 Frozen thresholds, seeds and timing
lockbox/core.py                        Access policy, event fusion, phases, outbox/ACK
lockbox/sensing.py                     Sensor validity, hysteresis and debounce
controllers/lockbox_controller/        Ordinary Robot; device adapter, no scene access
controllers/scene_supervisor/          Scenario actions and simulated alert endpoint
controllers/*_runner/                  Reproducible ground-truth test drivers
plugins/robot_windows/lockbox_window/   Local responsive dashboard; bundled Webots bridge
scripts/generate_worlds.py             Single model source for eight worlds
scripts/run_all.py                     Automated evaluation + hashes + reports
scripts/record_demo.py                 Native video capture and scenario verification
demo-studio/                          Editable Remotion scenes and recorded assets
```

See **`DESIGN.md`** for the state machine, sensing decisions, event protocol and failure behavior.

## Rebuild the videos

Requires Node.js 22+ and FFmpeg/ffprobe in addition to Webots. Clone the repo and download the complete release package if you want the existing raw footage; otherwise the recording command below recreates it. Videos already included can be watched without Node or Remotion.

```sh
cd demo-studio
npm ci
npx playwright install chromium
cd ..
python3 scripts/record_demo.py
python3 scripts/prepare_video_assets.py
cd demo-studio
npm run lint
npm run render:workflow
npm run render:recovery
npm run render:final
```

After rendering, return to the project root and run `python3 scripts/finalize_media.py` to check every encoded frame and refresh posters.

`npm run dev` opens editable video scenes. You can preview the opening, recorded run, and results separately. The native Webots capture is 1920×1080 at 31.25 fps. The control page is captured every three simulation steps through a token-protected loopback bridge; the same page handlers send the commands. Final videos are silent, 1920×1080, and 30 fps. `CAPTURE_CHROMIUM` can select an existing Chromium executable.

## Submission package

The [**complete project ZIP**](https://github.com/joejimenez-lab/parcel-guard-webots/releases/latest) includes the worlds, controller code, dashboard, design, final paper, presentation, speaker guide, proposal, reproducible tests, results, raw footage, editable video source, and all three finished demos. It excludes `node_modules`, caches, and temporary builds. Use this release asset for the complete handoff; GitHub's automatically generated source archive omits raw footage.

After extraction, run `python3 scripts/check_submission.py`. It uses only the Python standard library to verify the saved evidence, document/video hashes, raw-footage presence, and delivery manifest. It does not rerun the simulator. The runtime was also tested from an isolated copy, including the full Webots suite and a clean npm installation; see `results/portability_validation.json`.

Run `python3 scripts/package_project.py` to rebuild the unchanged delivery. If you rerun the evaluation or edit the documents, the saved submission hashes must be reviewed and refreshed before packaging. Keep a separate copy of the original release evidence when experimenting.

## Scope

One parcel at a time; local simulation with a simulated event endpoint. Demo PINs model roles, expiry, single use, replay rejection and cooldown. Real cloud authentication, Wi-Fi/TLS, outdoor weather and physical forced-entry resistance are outside the proposal scope. The event outbox survives simulated link loss but is volatile across controller restarts. The bolt is an actuator/feedback model, not a physical security certification. A plausible stuck-at sensor value is not automatically diagnosable from these devices alone.

## Additional checks and document rebuild

```sh
cd demo-studio
npm ci
npm run lint
cd ..
node tests/dashboard.cjs
python3 scripts/finalize_media.py
```

The dashboard also received a browser layout check at desktop and 390-pixel widths. DOM tests use recorded status and injected faults; the Webots runners exercise the controller and fixture.

The paper is authored in standalone LaTeX, with embedded vector diagrams, numbered equations, tables, and references. Install Tectonic or a working TeX distribution, then run `python3 scripts/build_submission.py` (set `TEX_BIN` if necessary). The script refreshes numerical evidence in `docs/parcel_guard_report.tex` from passing reports and exports the final PDF. `docs/FINAL_REPORT.md` is a repository reading companion. Edit the PPTX directly to revise the slides. The included PDF slide copy is a rendered viewing copy.
