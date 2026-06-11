---
score: 9
feedback: >-
  Excellent attempt. The attempt validates the new
  `psynet-participant-quality-telemetry` skill by applying it to a local
  text-heavy PsyNet experiment with timing, paste, focus/visibility,
  keydown/edit telemetry, attention-check status, simulated participant
  profiles, exported PsyNet-shaped data, and a conservative manual-review
  script. The report and participant video make the telemetry workflow
  reviewable, and the flagging rules correctly avoid claiming that telemetry
  proves AI use or bot use. Main improvement would be to test the skill on a
  richer real experimental paradigm with more ambiguous participant profiles,
  so the review rules face less cleanly separated cases.
---

# Evaluation

## Summary

Excellent attempt that validates the new
`psynet-participant-quality-telemetry` skill in a local text-heavy PsyNet
experiment. The telemetry workflow is reviewable, conservative, and supported
by participant evidence, exported PsyNet-shaped data, and a manual-review
script.

## Strengths

- Applies the telemetry skill to timing, paste, focus/visibility, keydown/edit,
  and attention-check signals.
- Includes simulated participant profiles, exported PsyNet-shaped data, a
  conservative review script, a report, and participant video evidence.
- Correctly avoids claiming that telemetry proves AI use or bot use.

## Weaknesses

- The simulated profiles are cleanly separated; a richer real experimental
  paradigm with more ambiguous participant profiles would stress-test the review
  rules more realistically.

## Criteria

- [x] The attempt explicitly uses or follows the `psynet-participant-quality-telemetry` skill.
- [x] It is runnable locally in PsyNet.
- [x] It records timing, attention/comprehension, paste/focus or tab-switch, and at least one text-production telemetry signal.
- [x] It simulates multiple participant profiles with at least one plausible and one suspicious profile.
- [x] It exports or provides PsyNet-format data.
- [x] It includes a transparent manual-review flagging script.
- [x] It avoids claiming that telemetry proves AI use or bot use.
- [x] It includes participant-facing evidence and a report explaining signal limitations.

## Notes

- Evaluator score: 9/10.
