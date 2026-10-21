# Similarity, discrimination, and identification experiment

This PsyNet experiment uses simple color-circle stimuli to compare three related psychophysics tasks:

- same-different discrimination for identical and documented different pairs;
- 0-6 similarity ratings for all unordered stimulus pairs with replacement;
- multi-item identification with set sizes 3, 4, and 5, alternating probe-present and probe-absent trials.

The implementation uses `StaticNode` definitions and `StaticTrialMaker` scheduling for each block. Each trial begins with a 500 ms fixation cross, uses fixed 1 s stimulus presentation, and includes a 750 ms retention delay before responses are enabled. Visual displays are implemented with PsyNet `GraphicPrompt` frames rather than custom JavaScript.

## Stimuli and sampling

The initial stimulus set contains six filled circles that vary primarily in color. Each stimulus record stores an extensible `dimensions` dictionary with `color`, `hue_deg`, and `size`, so later versions can add dimensions such as size while retaining the same metadata shape.

Identification trials store numbered display items, display positions, probe stimulus metadata, probe-present status, the intended correct item for present probes, and the nearest item for lure probes. This is enough to reconstruct the visual display from exported trial rows.

## Minimal review mode

Set `PSYNET_PROFILE=minimal` before launching the experiment to shorten the flow to one representative trial per psychophysics block and one Ishihara plate for visual review or participant evidence recording. The default profile is the canonical full design.

## Analysis

Run `python analysis.py` to generate summaries from a deterministic simulated dataset, or `python analysis.py --input <export-dir-or-trial-csv>` to summarize exported data. Outputs include a similarity matrix, same-different accuracy and reaction times, identification confusion probabilities, reaction-time summaries, and stimulus hue-distance diagnostics.
