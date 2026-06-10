---
score:
---

# Evaluation

## Summary

Awaiting human evaluation. This retry attempt was created to address the prior
attempt's weak participant video and low bot completion. The submitted evidence
now includes a reviewed participant video that progresses through all sections
to completion, plus a final performance test with 83 successful bot completions,
0 bot failures, 0 request errors, and 40 replacement bots still running at the
5-minute cutoff.

## Strengths

- Participant evidence video was reviewed and shows same-different trials,
  similarity trials, multi-item identification, Ishihara entries, demographics,
  and final completion without early termination.
- The performance path was redesigned from many server-side trial pages to three
  client-side block pages, improving the final 40-bot performance run from the
  previously evaluated 4 successful bots to 83 successful bot completions.
- Exported data include reconstructed trial-level rows for all client-side
  trials, plus participant and stimulus manifest tables.

## Weaknesses

- The block-page design disables PsyNet's page-level progress bar because it is
  misleading for multiple client-side trials within one page.
- The final performance run still had 40 replacement bots running at the
  5-minute cutoff, though 83 bots completed successfully and no bots failed.

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
  `performance.json`, simulated and exported analysis CSVs, and targeted
  screenshots.
- `participant.mp4` is visual-only. The experiment has no audio stimuli, and no
  audio-sensitive evidence is required.
- Video review confirmed that `participant.mp4` shows all task blocks, Ishihara,
  demographics, and final completion, with no obvious visual issues.
- Final performance evidence: 123 bots started, 83 bots succeeded, 0 bots
  failed, 40 replacement bots were incomplete at the 5-minute cutoff, 0 bot
  errors, and 0 request errors.
