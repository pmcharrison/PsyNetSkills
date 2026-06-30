# Report

## Summary

Implemented a self-contained PsyNet decision-making experiment in
`code/decision_making_study/`. Participants see two side-by-side options on six
independent trials, compare the same fixed five-feature set for both options in
every task, and choose one option per trial. The saved response values are stable identifiers
(`option_a`, `option_b`) while the participant-facing labels are translated.

## Translation readiness

- Source locale: English (`en`).
- Supported locales: English, Hindi (`hi`), and French (`fr`).
- Participant-facing strings are marked with PsyNet's `_ = get_translator(...)`
  pattern.
- `psynet translate hi fr` generated `locales/experiment.pot` and verified that
  complete non-fuzzy Hindi and French `.po` files need no additional machine
  translation.
- No real translator, recruiter, AWS, Prolific, or other production credentials
  were used.

## Validation

- `python -m py_compile experiment.py trial_manifest.py` passed.
- `python experiment.py` passed.
- `psynet translate hi fr` passed.
- `psynet test local` passed with 12 bots.
- `psynet simulate` produced 12 simulated participants and 72 finalized choice
  trials.
- `psynet performance-test local --n-bots 40 --duration-minutes 5
  --time-factor 1.0` completed with zero bot errors and wrote
  `evidence/performance.json`.
- Playwright participant-flow checks passed in English, Hindi, and French and
  produced screenshots plus MP4 screen recordings.

## Evidence

- `evidence/participant_en.mp4`: English participant flow.
- `evidence/participant_hi.mp4`: Hindi participant flow.
- `evidence/participant_fr.mp4`: French participant flow.
- `evidence/screenshots/`: ad, welcome, instructions, representative choice,
  thank-you, and finish screenshots for all three locales.
- `evidence/data.zip`: zipped `psynet simulate` export.
- `evidence/monitor.html`: local PsyNet dashboard snapshot.
- `evidence/performance.json`: sustained local performance-test metrics.
- `evidence/analyses/`: simulated-data summaries and notebook.

## Remaining metadata

The implementation and first-pass evidence are complete. `agent.json` remains
open because the human author GitHub username has not yet been provided.
