---
score:
---

# Evaluation

## Summary

Human evaluator to complete. This attempt includes a runnable local PsyNet experiment, local generated audio, participant video evidence, bot/performance checks, exported and simulated PsyNet-format data, and an analysis report. Bot/simulated outputs are documented as workflow validation only.

## Strengths

- Human evaluator to complete.

## Weaknesses

- Human evaluator to complete.

## Criteria

- [ ] The experiment must be runnable in PsyNet and use local/demo audio only.
- [ ] It must save time-stamped continuous or repeated emotion ratings linked to stimulus IDs.
- [ ] It must include at least two emotion dimensions, such as valence and arousal.
- [ ] It must include bot/local validation evidence and participant-facing video or browser evidence.
- [ ] It must export data or provide exported/simulated PsyNet-format data.
- [ ] It must include an analysis script summarizing trajectories by stimulus and condition.
- [ ] It must not claim real emotion-science results from bot/simulated participants.

## Notes

- Local dashboard export was collected by direct authenticated dashboard download because `psynet export local` failed to read explicit password flags without a configured `dashboard_password`.
- `evidence/data.zip` contains the local dashboard export, deterministic simulated PsyNet-format JSONL, and analysis outputs.
- Score and feedback should come from a human evaluator, captured conversationally when working with Cursor Cloud Agents.
