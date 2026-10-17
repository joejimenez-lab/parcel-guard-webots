# Presentation guide

The deck follows the final-report order and retains the proposal's suggested 13-minute talk plus two minutes for questions. The time limit is a proposal plan, not a newly confirmed course requirement. Speaker notes in the PPTX contain the explanations and source references.

## Running order

| Time | Slide | Speaker | Purpose |
|---|---:|---|---|
| 0:00–0:30 | 1 | Joshua | Introduce Parcel Guard and the team |
| 0:30–1:15 | 2 | Joshua | Explain parcel presence versus measured closure |
| 1:15–1:45 | 3 | Joshua | Describe the responsibility allocation |
| 1:45–2:30 | 4 | Joshua | Compare published workflows and justify the tools |
| 2:30–3:35 | 5 | Joe | Follow the data flow; separate detector and fixture |
| 3:35–4:35 | 6 | Joe | Explain actual device readings and filtering |
| 4:35–5:40 | 7 | Brandon | Explain credentials, motor sequence and timeouts |
| 5:40–6:35 | 8 | Joe | Play the 42-second delivery video |
| 6:35–7:40 | 9 | Brandon | Explain scenarios, denominators and fixed configuration |
| 7:40–8:50 | 10 | Brandon | Interpret the matrix and baseline limitations |
| 8:50–10:00 | 11 | Brandon | Explain failures found, corrections and regressions |
| 10:00–11:05 | 12 | Joe | Play the 54-second recovery video |
| 11:05–12:10 | 13 | Brandon | State limits and concrete next tests |
| 12:10–13:00 | 14 | Brandon | Conclude, identify evidence and invite questions |
| 13:00–15:00 | 14 | All | Questions and follow-up examples |

## Before presenting

Open both MP4 files locally and check their playback on the presentation computer. The videos are silent and captioned. Keep `output/index.html` open as a gallery and the PDF slides as a fallback. The PPTX includes stills and speaker notes; videos are supplied as separate files, not embedded media objects.

For a live demonstration, open `worlds/delivery_box.wbt` and its Robot Window. Use real-time speed. The simulation clock controls expiry, so leaving fast mode running can expire a courier code before the demonstration. Start a fresh scene with the parcel outside. The scenario buttons intentionally operate the test fixture.

## Live demonstration sequence

1. Select Courier, enter `2468`, and unlock. Wait for an open door and a retracted bolt.
2. Place the parcel, observe parcel detection, then close. Wait for `SECURED` and the delivery event.
3. Retry the courier code with a new request. Explain the used-code denial.
4. Select Owner, enter `1357`, unlock, remove the parcel, and close.
5. Disconnect the link. Apply impacts more than one simulated second apart. Restore the link and observe acknowledgments draining the queue.
6. Start a new session to issue fresh one-use codes. Unlock as owner, wait until the door has settled open, block the bolt, and close. A bolt fault should appear after two seconds. Release the bolt and wait for measured recovery.
7. Optional: start another new session, unlock as owner, wait until fully open, and block the door. Let the 20-second grant expire. A door fault appears after three more seconds. Release the door and watch it close before the bolt extends.

## Questions to prepare for

**Why is the reported queue delay zero?** The controller samples the event and inserts it into the outbox in the same simulation iteration. Sampling runs every 32 ms. The independent stimulus-to-observer measurement is at most 0.224 simulated seconds in the saved run. Real transport latency is outside that metric.

**Does 100% prove it works in the real world?** No. The cases are generated within a specified parcel envelope and the same scene families. We report the number of trials with each score. More varied shapes, disturbances, attackers and hardware would need new tests.

**Why does the baseline score only 0.10?** It is a simple motion alarm that cannot label delivery or retrieval. Every test sequence contains motion, so it flags them all. It illustrates the need for context in these scenes, and is not a comparison with an optimized classifier.

**Does the Supervisor tell the detector the answer?** The detector uses an ordinary `Robot` and reads devices. The Supervisor changes parcel placement and motor conditions. Truth labels remain in the test runner.

**How is exactly-once delivery achieved?** Packets can repeat. The endpoint records each `(session, ID)` once and acknowledges duplicates. The claim is unique processing of retained events during simulated outages, not exactly one network transmission or durable restart recovery.

**What happens if the door is held open?** The grant ends at its deadline. The door is commanded closed, the bolt stays retracted, and failure to close triggers a fault. Parcel movement after expiry is unapproved. Release leads to measured recovery.

**What happens on a restart?** The current queue, replay cache and token-use state are volatile. Restart persistence is future work. The JSONL file is an export, not a recovery database.

**Can an attack occur during approved access?** Yes. Approved motion and brief settling intervals suppress the impact rule. The report identifies adversarial handling during those intervals as an untested limitation.

**When is delivery recorded?** Parcel placement creates `parcel_detected` and pending status. The delivery event follows measured door closure and bolt locking. If the bolt jams, delivery remains pending until recovery; removal or tampering cancels it.

**Can either code be reused?** No. Both temporary tokens are consumed on grant. New session is a test control that reissues the demo credentials.

**What changed during the review?** Delivery now waits for lock feedback, both temporary tokens work once, and reset with an open door keeps the bolt retracted. Expired authorization and early-close handling were corrected; sensor startup and gaps now require stable data; status JSON handles unavailable values; and physical hinge stops bound unpowered travel. A failed stop-placement experiment is retained in `results/hinge_contact_diagnostic.json`.

Listen to the complete question, answer it directly, then show one relevant observation or test. If the evidence does not answer it, explain the test needed instead of guessing.

## Complete walkthrough

`output/Parcel Guard - Final Demonstration.mp4` combines both scenarios and the final evaluation summary in 94 seconds. It is captioned without narration. The two shorter clips remain timed to slides 8 and 12. The standalone paper source is `docs/parcel_guard_report.tex`.
