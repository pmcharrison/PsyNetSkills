# Cross-cultural masked affective priming demo

This folder contains a self-contained PsyNet implementation of the
cross-cultural masked affective priming challenge. The participant sees a rapid
sequence of fixation, forward mask, emotional prime, backward mask, and
ambiguous target face, then classifies the target as happy or angry.

The committed stimuli are generated SVG placeholders for local validation only.
They are not validated face stimuli and should not be interpreted as evidence
about real cultural groups. Replace `data/manifest.json` and the SVG files in
`data/stimuli/` with validated stimulus assets for a real study while preserving
the metadata fields used by `experiment.py`.

## Local commands

- `python3 generate_demo_stimuli.py`
- `python3 experiment.py`
- `psynet test local`
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output ../../evidence/performance.json`
- `python3 analyze.py --input ../../evidence/simulated_trials.json --output ../../evidence/analyses/priming_summary.csv`

