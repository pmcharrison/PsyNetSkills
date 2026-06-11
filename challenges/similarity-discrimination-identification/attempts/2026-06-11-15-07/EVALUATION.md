---
score:
---

# Evaluation

## Summary

Pending human evaluation.

## Strengths

- Pending human evaluation.

## Weaknesses

- Pending human evaluation.

## Criteria

- [ ] The experiment runs locally in PsyNet and presents a coherent participant flow with instructions, fixation, task trials, the Ishihara test, demographics, and a completion screen.
- [ ] The stimulus implementation uses simple visual items varying in color and stores structured metadata that can be extended to additional dimensions such as size.
- [ ] The same-different discrimination block includes identical and different pairs, records 2AFC responses, computes accuracy, and stores reaction times.
- [ ] The similarity block presents all required stimulus pairs and records 0-6 Likert ratings with endpoint labels, pair metadata, and reaction times.
- [ ] The multi-item identification block implements set sizes 3, 4, and 5, numbered items around fixation, fixed presentation and delay durations of at least 500 ms, probe-present and probe-absent trials, response collection, correctness metadata, confusion records, and reaction times.
- [ ] Trial-level data are sufficient to reconstruct every presented display, including stimulus identities, visual attributes, display positions, timing parameters, probes, responses, accuracies, and reaction times.
- [ ] The Ishihara and demographics measures are administered at the end of the experiment and their outputs are saved.
- [ ] The included analysis script or notebook runs on exported or simulated data and summarizes similarity matrices, discrimination performance, identification confusion probabilities, and reaction-time distributions.
- [ ] The implementation avoids real service credentials and uses only local, reproducible configuration suitable for PsyNet development and review.

## Notes

- Criteria copied after implementation and evidence collection.
- `evidence/participant.mp4` is a focused minimal-profile recording of the three core task blocks; `evidence/data.zip` comes from a completed minimal-profile participant including Ishihara and demographics.
