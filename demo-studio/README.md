# Parcel Guard video studio

Three complete videos and their separately editable opening, recorded-simulation and evidence scenes are registered in `src/Root.tsx`. This is presentation code; the mechanism footage is recorded in Webots.

From the project root, run `python3 scripts/prepare_video_assets.py` first. It verifies the native recording assertions and copies footage plus telemetry into `public/`. The portable ZIP omits the duplicate `public/*.mp4` copies; this preparation command recreates them from `output/raw/`.

```sh
cd demo-studio
npm ci
npm run lint
npm run dev
npm run render:workflow
npm run render:recovery
npm run render:final
```

Node 22+ is recommended. Package versions are locked. No web fonts, music, external images or cloud assets are required. Native recordings are silent. Scene text and all graphical motion use the Remotion frame clock.

`RecordedScene.tsx` looks up the latest recorded status at each video timestamp. The caption band shows door angle, bolt travel, parcel state, message counts, and the latest event. Chapter text comes from the recording metadata; pending-delivery wording follows the recorded policy flag. Status was published every 96 ms, so readings may lag physical motion by that interval. The original telemetry remains in `results/`.

The closing results tables summarize the fixed, passing evaluation delivered with this project. If changing the controller/evaluation, regenerate the reports and update the evidence scene to match any changed results before exporting.
