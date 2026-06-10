---
score:
---

# Evaluation

## Summary

Summarize the human evaluator's overall judgment.

## Strengths

-

## Weaknesses

-

## Criteria

- [ ] The experiment runs locally in PsyNet and presents a coherent participant
  flow with instructions, fixation, task trials, the Ishihara test,
  demographics, and a completion screen.
- [ ] The stimulus implementation uses simple visual items varying in color and
  stores structured metadata that can be extended to additional dimensions such
  as size.
- [ ] The same-different discrimination block includes identical and different
  pairs, records 2AFC responses, computes accuracy, and stores reaction times.
- [ ] The similarity block presents all required stimulus pairs and records 0-6
  Likert ratings with endpoint labels, pair metadata, and reaction times.
- [ ] The multi-item identification block implements set sizes 3, 4, and 5,
  numbered items around fixation, fixed presentation and delay durations of at
  least 500 ms, probe-present and probe-absent trials, response collection,
  correctness metadata, confusion records, and reaction times.
- [ ] Trial-level data are sufficient to reconstruct every presented display,
  including stimulus identities, visual attributes, display positions, timing
  parameters, probes, responses, accuracies, and reaction times.
- [ ] The Ishihara and demographics measures are administered at the end of the
  experiment and their outputs are saved.
- [ ] The included analysis script or notebook runs on exported or simulated data
  and summarizes similarity matrices, discrimination performance, identification
  confusion probabilities, and reaction-time distributions.
- [ ] The implementation avoids real service credentials and uses only local,
  reproducible configuration suitable for PsyNet development and review.

## Notes

- Score and feedback should come from a human evaluator, captured
  conversationally when working with Cursor Cloud Agents.
- Evidence collected includes `participant.mp4`, `monitor.html`, `data.zip`,
  `performance.json`, simulated analysis CSVs, and targeted UI screenshots.
- `participant.mp4` is visual-only. The experiment has no audio stimuli, and the
  Cursor Cloud VM did not expose PulseAudio `pactl`; no audio-sensitive evidence
  is required for this task.
- Local export was run with `--no-source` to avoid an interactive dashboard
  credential prompt. The complete source code is committed under `code/`.
