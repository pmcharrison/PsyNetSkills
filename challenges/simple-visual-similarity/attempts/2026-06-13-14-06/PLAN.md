# Plan

## Science

The experiment will measure explicit similarity judgments for simple visual stimuli. Each data point will pair two colored circles with a 1-5 rating and a reaction time, enabling a similarity matrix and response-time summary over stimulus pairs.

## Methods

Participants will first read brief instructions explaining that they will see two colored circles and rate how visually similar the pair appears. The stimulus set will contain four fixed-size colored circles: red, green, blue, and yellow. With four stimuli, the unordered pair set including identical pairs contains exactly 10 pairs, so each participant can see every pair once while satisfying the requirement for 10 random trials.

Each trial will begin with a centered fixation cross. After the fixation interval, two circles will appear simultaneously at fixed left and right positions. Participants will then rate similarity on a 5-point Likert scale labeled from 1 = Completely Dissimilar to 5 = Completely Similar. The response interface will support both mouse clicks and the numeric keyboard keys 1-5. Trial order will be randomized independently for each participant, while the pair identity, left/right stimulus identities, rating, and reaction time will be stored for every trial.

The initial analysis will read a simulated PsyNet export, aggregate ratings by unordered pair, and display the mean similarity ratings as a heatmap. It will also compute mean reaction time for each pair and present a table or companion heatmap for response-time inspection.

## Implementation

The implementation will live under `code/simple_visual_similarity/` inside this attempt. I will start from PsyNet's static and graphics demos, using `StaticNode`, `StaticTrial`, and `StaticTrialMaker` for the 10 pair nodes and `GraphicPrompt` with `Frame` objects for the fixation and simultaneous circle display. The colored-circle definitions will be generated from a small structured stimulus list so later dimensions, such as size, can be added by extending the manifest fields rather than rewriting trial logic.

The trial page will use `KeyboardPushButtonControl` with choices `1` through `5` and keys `Digit1` through `Digit5`. The control will be inactive during the fixation frame and activated when the circle-pair frame begins, so reaction time reflects the interval from stimulus-pair onset to response as closely as PsyNet's native event system allows. The formatted answer and trial definition will preserve the rating, stimulus IDs, color values, pair ID, and response timing.

The timeline will include an instruction page, one static trial maker administering all 10 pair nodes in randomized order, and a final thanks page. The experiment will set a larger bot count for simulation evidence so `psynet simulate` exports enough rows for the analysis notebook.

Validation will proceed in this order after plan approval:

1. Run `python experiment.py` from the experiment directory to verify the manifest and generated pair count.
2. Run `psynet test local` to confirm an end-to-end bot participant completes all 10 trials and records the intended fields.
3. Run `psynet simulate` and save the export as `evidence/simulated_data.zip`.
4. Create `evidence/analyses/analysis.ipynb` that reads the exported CSV files directly, builds the rating heatmap, and summarizes reaction times by pair.
5. Run participant-flow recording and targeted screenshots via the repository evidence workflow.
6. Run `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output <attempt>/evidence/performance.json`.
7. Write `REPORT.md`, update `TIMELINE.md`, and complete `agent.json` once all evidence is collected.
