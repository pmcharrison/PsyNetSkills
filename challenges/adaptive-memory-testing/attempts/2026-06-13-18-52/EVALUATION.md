---
score:
---

# Evaluation

## Summary

Human evaluation has not started. The implementation and first-pass evidence collection are complete, with two explicit warnings: author metadata is pending, and performance/HMC-comparison results reveal limitations in the current adaptive policy.

## Strengths

- Implements a runnable PsyNet adaptive digit-memory experiment with exact scoring and exported adaptive metadata.
- Includes PsyNet bot validation, Playwright participant evidence, dashboard monitor HTML, simulated export, executed analysis notebook, and standalone simulation diagnostics.
- Hidden criteria evidence is present: 30 adaptive participants, 30 non-adaptive participants, and HMC accuracy comparison.

## Weaknesses

- The HMC comparison shows worse ability-estimate accuracy for the adaptive policy than for the random baseline in the completed synthetic run.
- The 40-bot performance test shows load pressure and no bot completions within five minutes.
- Human author GitHub metadata is still missing from `agent.json`.

## Criteria

- [x] Tests include an adaptive simulation with 30 participants.
- [x] Tests include a non-adaptive simulation with 30 participants.
- [x] The test fits the adaptive model using HMC.
- [x] The test reports a comparison of participant memory-ability estimate accuracy under adaptive and non-adaptive simulations.

## Notes

- HMC mean absolute error: adaptive = 2.5594, non-adaptive = 1.6519.
- HMC RMSE: adaptive = 2.6125, non-adaptive = 1.8983.
- Score and feedback should come from a human evaluator, captured conversationally when working with Cursor Cloud Agents.
