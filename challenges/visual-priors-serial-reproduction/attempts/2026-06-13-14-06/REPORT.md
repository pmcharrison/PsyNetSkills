# Report

## Implementation

The attempt implements a runnable PsyNet experiment for the visual-priors serial reproduction task. The experiment presents a timed dot inside a geometric outline, inserts a blank retention interval, and asks the participant to reproduce the remembered dot location by clicking inside the same shape. The response is saved as normalized shape-local coordinates and becomes the target location for the next node in the chain.

The implementation uses explicit PsyNet chain architecture:

- `SpatialMemoryNode` carries the current chain state and creates the next node from the completed trial answer.
- `SpatialMemoryTrial` presents the participant-facing memory task.
- `SpatialMemoryTrialMaker` administers 12 across-participant chains: two seed chains for each of the circle, triangle, square, vertical oval, horizontal oval, and pentagon.
- Each chain is configured for 10 generations, matching the serial reproduction design described in the challenge source.

The UI uses an SVG page with timed stimulus display, blank delay, click/reclick response, and immediate accuracy feedback. Each memory page has a unique session ID so PsyNet reloads the browser page and installs the SVG click handlers for every trial.

## Simulation and analysis

`psynet simulate` completed successfully and produced `evidence/simulated_data.zip`. The simulated export contains:

- 10 bots
- 12 `SpatialMemoryNetwork` rows
- 132 `SpatialMemoryNode` rows
- 120 `SpatialMemoryTrial` rows

The canonical analysis notebook is `evidence/analyses/analysis.ipynb`. It reads `SpatialMemoryTrial.csv` directly from the zip export, summarizes trials by shape and generation, and plots initial targets together with final-generation reproductions for all six shape conditions.

## Validation

Functional validation passed with `python experiment.py` and `psynet test local`. The bot test asserts that each bot completes all 12 chain trials, answers remain inside the appropriate shapes, 120 chain trials are collected, and every shape reaches the final generation.

Performance validation passed with `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0`. The JSON output is saved as `evidence/performance.json`, with the command log in `evidence/performance-test.log`.

## Participant-flow evidence

The participant flow was exercised with Playwright against a local `psynet debug local` server. Evidence includes:

- `evidence/screenshots/01_instructions.png`
- `evidence/screenshots/02_stimulus_display.png`
- `evidence/screenshots/03_response_feedback.png`
- `evidence/screenshots/04_experimental_feedback.png`
- `evidence/participant.mp4`

The recording shows the instructions, timed stimulus display, blank delay, click response, feedback, representative experimental chain trials, and completion flow. The experiment has no audio, so the participant MP4 is visual-only.

## Notes

The local dashboard route `/dashboard/monitor` returned 404 in this PsyNet checkout, so `evidence/monitor.html` contains the authenticated dashboard landing page captured from the running local experiment.
