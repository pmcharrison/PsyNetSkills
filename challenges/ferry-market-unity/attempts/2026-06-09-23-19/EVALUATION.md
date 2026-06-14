---
score: 8
---

# Evaluation

## Summary

Awaiting human evaluator judgment. Current implementation is functionally
verified in a GUI participant run: PsyNet launches, the Unity WebGL build loads,
three Unity trials run via `max_trials_per_participant=3`, and the participant
reaches the final completion page.

## Strengths

- Uses PsyNet `MainConsent`, instructions, `UnityPage`, a three-trial `StaticTrialMaker`, and a final completion page.
- Serves the provided Unity WebGL build from PsyNet's expected `/static/scripts/` layout.
- Matches the original experiment's `ferry_*` JSON payload contract and documents that `ferry_speeds` are delays.
- Includes a browser participant runner with rapid `ArrowUp` and sparse side-key corrections.
- GUI testing completed all three Unity trials and reached the final 100% Finish page.

## Weaknesses

- The saved video artifact is a screenshot slideshow rather than a continuous recording because the screen recorder failed to save the long live run.
- The headless Playwright path still needs further tuning; GUI-driven testing completed successfully.
- `evidence/data.zip`, `evidence/monitor.html`, and performance evidence are not yet collected.

## Criteria

No separate `CRITERIA.md` file was provided with this challenge.

## Notes

- `psynet test local` exercises the synthetic PsyNet bot response and passes.
- The successful participant behavior is documented in `evidence/participant-flow-summary.md`, screenshots, and the slideshow MP4.
