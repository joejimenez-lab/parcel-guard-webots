# Parcel Guard submission


## Progress Report 2 handoff

Use the report, 20-slide PDF and ZIP packages from [release v2.6.0](https://github.com/joejimenez-lab/parcel-guard-webots/releases/tag/v2.6.0) for the current classroom handoff. The original Progress Report 2 release is archived in [v2.5.0](https://github.com/joejimenez-lab/parcel-guard-webots/releases/tag/v2.5.0).

The current classroom files are in `output/progress-report-2/`. Submit the written paper PDF, present the editable 20-slide deck from the chat viewer, and keep its slide PDF as a playback backup. Export the deck as PowerPoint from the viewer if a local PPTX is required. `output/Parcel Guard - Progress Report 2 - Submission.zip` bundles the PDFs, speaker guide, live demo guide and editable report source.

- Written paper: `output/pdf/Parcel Guard - Progress Report 2.pdf`
- Slide viewing copy: `output/pdf/Parcel Guard - Progress Report 2 Slides.pdf`
- Speaker guide: `docs/PROGRESS_REPORT_2_PRESENTATION_GUIDE.md`
- Live demo: `docs/PROGRESS_REPORT_2_DEMO.md`
- Canonical report source: `docs/parcel_guard_progress2_report.tex`
- Report rebuild: `python3 scripts/build_progress2_report.py` with a TeX distribution and IEEEtran installed
- Source/evidence package: `output/Parcel Guard - Progress Report 2 - Project.zip`
- Full workflow diagram: [PNG](docs/assets/parcel-guard-workflow.png), also included in the report appendix and on slides 19–20. Slide 5 shows the lost-ACK test with both controllers restarting.

Use the password-only owner workflow. The older final paper, deck, videos and original submission checker below belong to the earlier delivery. Current evaluated source/report hashes are in `results/evaluation_manifest.json`; each current ZIP has its own file manifest.

## Earlier submission

**Team:** Joshua Guico, Joe Jimenez, Brandon Lopez

**Course:** CS 5650 · Fall 2026

**Instructor:** Dr. Jung Soo Lim

## What to submit

The assignment requires a paper as a PDF and a class presentation. Use the files below after the submission check passes.

| Purpose | File |
|---|---|
| Paper for the documentation assignment | [Final report PDF](output/pdf/Parcel%20Guard%20-%20Final%20Report.pdf) |
| Class presentation, including speaker notes | [Final presentation PPTX](output/submission/Parcel%20Guard%20-%20Final%20Presentation.pptx) |
| Presentation fallback | [Slide PDF](output/pdf/Parcel%20Guard%20-%20Final%20Presentation.pdf) |
| Complete captioned walkthrough | [Final Demonstration MP4](output/Parcel%20Guard%20-%20Final%20Demonstration.mp4) |
| Editable paper source | [Standalone LaTeX](docs/parcel_guard_report.tex) |
| Delivery and retrieval demo | [Delivery Workflow MP4](output/Parcel%20Guard%20-%20Delivery%20Workflow.mp4) |
| Access failures, outages, and recovery demo | [Security Recovery MP4](output/Parcel%20Guard%20-%20Security%20Recovery.mp4) |
| Complete source, evidence, and media | **Parcel Guard - Complete Project.zip** from the [public release](https://github.com/joejimenez-lab/parcel-guard-webots/releases/tag/v2.4.0) |

Submit the report PDF to the documentation assignment. Use the PPTX for the class presentation and keep the two short MP4 clips on the presentation computer. The videos are separate files; the deck includes stills and notes explaining when to play them. The source ZIP and repository are supporting materials for any code or project attachment requested by the instructor.

The supplied assignment shows the due date as TBD. It gives no upload-size limit or confirmed talk length. The speaker guide follows the proposal's suggested 13-minute talk and two-minute Q&A. Check the course page for scheduling updates before uploading.

## Check the downloaded project

Extract the complete ZIP and keep its folders together. From the extracted **Parcel Guard** folder, run:

```sh
python3 scripts/check_submission.py
```

Python 3.10+ is sufficient for this check. It verifies the saved test reports, evaluated source, submission documents, all three videos, raw-footage presence, and every file in the delivery manifest. It does not run Webots or re-grade the project. A GitHub source-code ZIP omits raw footage; use the attached **Complete Project** ZIP for the full handoff.

To repeat the simulator tests, use `python3 scripts/run_all.py`. This writes a new set of results, so do it in a separate copy if you want to retain the release's original evidence and document hashes.

## Before class

1. Rehearse with the [speaker guide](docs/PRESENTATION_GUIDE.md). Each presenter should be able to explain their assigned modules, the measurements, and the stated limits.
2. Play the final walkthrough and both short clips locally. They are silent and captioned; no internet connection is needed for playback.
3. Keep `output/index.html` open for convenient video playback and keep the slide PDF available.
4. For a live demo, open `worlds/delivery_box.wbt` in Webots R2025a, choose real-time speed, and open its Robot Window. Start a fresh scene with the parcel outside.
5. Use courier code `2468` and owner code `1357`. Both codes are single-use. The courier code expires after 300 simulated seconds; the owner code expires after 86,400 seconds. Start a new session before repeating an access cycle. Follow the full sequence in the speaker guide.

## Evidence and coverage

- [Proposal and rubric coverage](REQUIREMENTS.md)
- [Recorded evaluation results](results/REPORT.md)
- [System design](DESIGN.md)
- [User guide and troubleshooting](docs/USER_GUIDE.md)

The submission check catches missing files and stale exports. After it passes, upload the report PDF and prepare the presentation using the speaker guide.
