# Similarity, discrimination, and identification experiment

This attempt implements a PsyNet experiment with three visual blocks using simple filled circles whose primary perceptual dimension is color. Stimulus definitions live in `data/stimuli.json`; each stimulus already stores its dimensions as structured metadata so future versions can add dimensions such as size without changing the trial schema.

## Blocks

- Same-different discrimination: identical and different pairs, randomized by `StaticTrialMaker`, with response, accuracy, and reaction time saved per trial.
- Similarity judgment: all unordered pairs including identical anchors, rated from 0 to 6 with endpoint labels.
- Multi-item identification: set sizes 3, 4, and 5, numbered displays around a central fixation cross, probe-present and probe-absent trials, nearest-item scoring, and full display reconstruction metadata.

Every trial begins with a fixation frame. The stimulus display then appears for a fixed duration, disappears for a fixed delay of at least 500 ms, and only then are responses enabled. Identification trials show the probe after the delay while the prior display remains absent.

Set `PSYNET_PROFILE=minimal` for short visual evidence runs. The default profile uses the full documented trial set. Minimal mode shortens the three task blocks and relaxes the color-vision pass threshold so manual recordings can continue to demographics even when randomized Ishihara plate order is not known to the operator.

## Analysis

Run `python analysis.py --output evidence/analysis-summary.json` to analyze the documented simulated dataset. The script reports the similarity matrix, discrimination accuracy and reaction-time summaries, identification confusion probabilities, and reaction-time summaries for all blocks.
