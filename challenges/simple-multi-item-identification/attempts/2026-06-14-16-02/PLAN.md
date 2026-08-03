# Plan

## Science

This experiment measures how accurately participants identify a briefly presented item from a small visual array when later shown a single probe. On identification trials, the probe is one of the original items and the task yields an objective identification accuracy score. On generalization trials, the probe is a new colored item and the response is interpreted as a similarity-based generalization choice, supporting confusion-probability summaries across the displayed stimuli.

## Methods

Participants will complete ten randomly sampled trials. Each trial will use a set size of three, four, or five items, with set size sampled across the session. The stimuli will be colored circles of fixed radius shown on a neutral white background. Each stimulus will have a stable item number and an x-y position arranged evenly around fixation. The stimulus definition will be structured as dictionaries with fields for color and radius so that later dimensions, such as size, can be added without changing the trial-recording format.

The trial sequence will be:

1. A fixation cross presented alone.
2. A numbered visual array presented around fixation for a fixed brief duration.
3. A blank interval of at least 500 ms.
4. A single probe circle presented at fixation or near the center with response controls enabled.

The probe condition will be either `identification` or `generalization`. For `identification` trials, the probe color will exactly match one item from the original set and the correct answer will be that item's number. For `generalization` trials, the probe color will be generated between or near the presented colors while avoiding exact equality, and the selected item number will be recorded as the participant's generalization choice without an accuracy score.

Responses will use numbered buttons labeled `1` through `N`, centered below the probe. Participants will be able to click the buttons or press the corresponding digit keys. Reaction time will be measured from probe onset to the button/key response.

For every trial, the saved answer will include the full stimulus set, item numbers, item positions, probe identity, probe condition, raw participant response, accuracy for match trials, and reaction time in milliseconds.

## Implementation

The experiment will be implemented as a self-contained PsyNet experiment under `code/simple_multi_item_identification/`, rather than directly in `code/`, to avoid colliding with Python's standard-library `code` module. The implementation will copy the minimal structure from PsyNet's local `hello_world` and static-trial demos, then add custom static trials for generated visual stimuli.

Core PsyNet constructs:

- `StaticNode` definitions for trial stimuli, set size, probe condition, probe item, item positions, and correct response metadata.
- A `StaticTrial` subclass whose `show_trial` returns a `ModularPage`.
- `GraphicPrompt` with multiple `Frame` objects for fixation, stimulus array, blank delay, and probe display.
- `KeyboardPushButtonControl` with choices `["1", ..., str(N)]` and keys `["Digit1", ..., f"Digit{N}"]`, preserving both keyboard and mouse responses.
- A custom control `format_answer` method that reads PsyNet's native event log, computes reaction time from the `responseEnable` event at probe onset to the final `pushButtonClicked` event, and returns a structured trial answer.
- A `StaticTrialMaker` configured for ten trials per participant.

Stimulus generation will be deterministic at node-construction time. The code will create a balanced pool across set sizes and probe conditions, then sample ten trials per participant from that pool. Colors will be represented as HSL or hex values, with helper functions for color interpolation and circular array positions. The representation will reserve fields such as `radius` and `features` so future non-color dimensions can be added cleanly.

The visual display will follow the psychophysics guidance: no extra labels or prompts inside the stimulus field beyond item numbers, no visible panel frame around the white stimulus area, no lingering fixation during probe response unless included in the probe frame by design, and neutral button styling.

Bot behavior will be implemented via `get_bot_response`, returning `BotResponse` metadata with a synthetic `responseEnable` and `pushButtonClicked` event pair so the same answer-formatting path records simulated reaction times. Identification-trial bots will usually choose the correct response; generalization-trial bots will choose the nearest color by circular hue distance.

Validation and evidence after plan approval will include:

- `python experiment.py` from the experiment directory.
- `psynet test local`.
- `psynet simulate` with enough bots to produce usable accuracy, confusion, generalization, and reaction-time summaries, saved as `evidence/simulated_data.zip`.
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output <absolute evidence path>`.
- A Playwright/ffmpeg participant-flow recording and targeted screenshots following the participant-video workflow.
- `evidence/analyses/analysis.ipynb`, executed in place and kept under the dashboard size limit, reading the simulated export directly and showing identification accuracy, lure choices, confusion probabilities, and reaction-time plots.
- `REPORT.md` summarizing implementation decisions, validation, simulation results, and any blockers.

## Human review

The human reviewer approved this plan after the terminology change from `match`/`lure` to `identification`/`generalization`.
