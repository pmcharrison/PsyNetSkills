---
score: 4
---

# Evaluation

## Summary

The human evaluator assigned a score of 4/10. The experiment code is present,
but the submitted evidence is weak: the participant video does not convincingly
show an agent attempting the experiment, and the performance test shows that only
4 of 44 started bots succeeded while 40 remained incomplete.

## Strengths

- The experiment code is present and can be reviewed.

## Weaknesses

- The participant video does not provide convincing evidence of a real
  experiment attempt; the evaluator reports that it appears to wait at the start
  page rather than progressing through the task.
- The performance evidence is poor: `performance.json` records 44 bots started,
  4 bots succeeded, and 40 bots incomplete.

## Criteria

- [ ] The experiment runs locally in PsyNet and presents a coherent participant
  flow with instructions, fixation, task trials, the Ishihara test,
  demographics, and a completion screen. Evaluator note: code exists, but the
  submitted video does not convincingly demonstrate the participant flow.
- [x] The stimulus implementation uses simple visual items varying in color and
  stores structured metadata that can be extended to additional dimensions such
  as size. Evaluator note: the code is present.
- [x] The same-different discrimination block includes identical and different
  pairs, records 2AFC responses, computes accuracy, and stores reaction times.
- [x] The similarity block presents all required stimulus pairs and records 0-6
  Likert ratings with endpoint labels, pair metadata, and reaction times.
- [x] The multi-item identification block implements set sizes 3, 4, and 5,
  numbered items around fixation, fixed presentation and delay durations of at
  least 500 ms, probe-present and probe-absent trials, response collection,
  correctness metadata, confusion records, and reaction times.
- [x] Trial-level data are sufficient to reconstruct every presented display,
  including stimulus identities, visual attributes, display positions, timing
  parameters, probes, responses, accuracies, and reaction times.
- [ ] The Ishihara and demographics measures are administered at the end of the
  experiment and their outputs are saved. Evaluator note: this is not
  convincingly demonstrated by the participant video.
- [x] The included analysis script or notebook runs on exported or simulated data
  and summarizes similarity matrices, discrimination performance, identification
  confusion probabilities, and reaction-time distributions.
- [x] The implementation avoids real service credentials and uses only local,
  reproducible configuration suitable for PsyNet development and review.

## Notes

- Score and feedback should come from a human evaluator, captured
  conversationally when working with Cursor Cloud Agents.
- Evidence collected includes `participant.mp4`, `monitor.html`, `data.zip`,
  `performance.json`, simulated analysis CSVs, and targeted UI screenshots, but
  the evaluator found the participant video insufficient.
- `participant.mp4` is visual-only and was judged not to show a convincing
  experiment attempt.
- `performance.json` should be read as weak performance evidence because only 4
  of 44 started bots succeeded and 40 were incomplete.
- Local export was run with `--no-source` to avoid an interactive dashboard
  credential prompt. The complete source code is committed under `code/`.
