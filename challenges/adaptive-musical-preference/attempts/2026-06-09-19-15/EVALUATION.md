---
score:
---

# Evaluation

## Summary

Awaiting human evaluation.

## Strengths

- 

## Weaknesses

- The 40-bot, 5-minute performance window completed with zero bot or request
  errors, but some bots were still running when the fixed-duration test ended.
  See `evidence/performance.json` for the concurrency results.

## Criteria

- [ ] The experiment implements genuine adaptive logic rather than a fixed random
  sequence of choices.
- [ ] Stimulus dimensions are documented and recoverable from saved metadata.
- [ ] Pairwise choice data can be reconstructed after the experiment.
- [ ] The participant experience is understandable and not overloaded with technical
  language.
- [ ] The analysis component produces a meaningful summary of preferences.
- [ ] Evidence includes either a local run, a bot/test run, or a clearly documented
  reason why runtime validation was blocked.

## Notes

- Score and feedback should come from a human evaluator, captured
  conversationally when working with Cursor Cloud Agents.
- `evidence/participant.mp4` records a full participant run with non-silent audio
  (`mean_volume: -22.6 dB`, `max_volume: -10.6 dB`), 12 non-identical pairwise
  choices, the preference summary, completion page, and recruiter exit.
