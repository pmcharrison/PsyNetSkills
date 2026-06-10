---
score:
feedback:
  - "The styling/phrasing for the popularity ratings / \"New\" label etc. should be identical to the original experiment."
  - "Generally, the phrasing should be identical, unless a change is necessary, such as referring to melodies rather than images."
---

# Evaluation

## Summary

The evaluator responded positively to the attempt overall, but flagged a
reference-parity issue: the participant-facing wording and styling should match
the original experiment wherever possible, with only necessary melody-domain
substitutions.

## Strengths

- The attempt was considered good enough to receive positive feedback.

## Weaknesses

- Popularity-rating styling and labels, including the "New" presentation, should
  be identical to the original experiment.
- Participant-facing phrasing should mirror the reference implementation unless
  a domain change is required, such as replacing image/drawing language with
  melody language.

## Criteria

Copied from `CRITERIA.md`; leave unchecked until a human evaluator reviews the
attempt.

### Core experiment parity

- [ ] **Must-have:** The experiment preserves the reference rolling-inventory
  imitation-chain structure, including adoption followed by creation on each
  round, fixed pool capacity with oldest-item removal, ancestry tracking, and
  popularity accounting.
- [ ] **Must-have:** The first participant round handles an empty market
  correctly by skipping adoption and allowing creation from scratch.
- [ ] **Must-have:** Later rounds require adoption before creation when the
  market is large enough, matching the reference enablement rules.
- [ ] **Must-have:** Both participant conditions are implemented: one with
  popularity information visible at adoption and one without.
- [ ] **Must-have:** Chain counts, trials per participant, pool size, and other
  core timing or network parameters match the reference implementation, or any
  intentional deviation is clearly documented in the attempt README.

### Music-domain interfaces

- [ ] **Must-have:** The creation interface is a 3x9 step sequencer with Do,
  Re, and Mi rows, distinct row colours, clickable note toggling, and support
  for overlapping notes within the same time slot.
- [ ] **Must-have:** The creation page includes a working **Play melody**
  control that audibly previews the current sequence before submission.
- [ ] **Must-have:** Market previews let participants listen to each melody via
  audio playback.
- [ ] **Must-have:** The market preview does not expose the underlying note
  grid.
- [ ] **Must-have:** Participants complete an audio pre-screening step before
  the main task by hearing a static voice clip saying "five" and typing the
  answer; `five` and `5` are accepted irrespective of letter case, and
  participants who cannot pass do not continue into the market task, unless the
  attempt documents and uses a more robust pre-screening solution found in the
  Computational Audition Lab GitLab group.
- [ ] **Nice-to-have:** Market previews include a waveform or similarly clear
  audio visualization.

### Validation, data, and robustness

- [ ] **Must-have:** Empty melodies are rejected.
- [ ] **Must-have:** Responses exceeding the allowed number of note changes are
  rejected, with separate limits for from-scratch and edit-from-adopted regimes
  analogous to the reference experiment.
- [ ] **Must-have:** Saved data are sufficient to reconstruct each submitted
  melody, adoption choice, inventory state updates, popularity counts,
  audio pre-screening outcome, and condition assignment.
- [ ] **Must-have:** The implementation does not include the reference
  experiment's mouse movement tracking, stroke event tracking, or drawing-specific
  interaction logs.
- [ ] **Must-have:** Instruction pages, recruitment text, post-task survey, and
  any instruction screenshots are adapted for melodies rather than drawings
  while preserving the reference debrief structure.
- [ ] **Must-have:** `psynet test local` passes with local defaults and no real
  production credentials.

### Evidence

- [ ] **Must-have:** Evidence shows the participant audio pre-screening step.
- [ ] **Must-have:** Evidence shows audio playback during market preview.
- [ ] **Must-have:** Evidence shows step-sequencer composition or editing with
  **Play melody** working.
- [ ] **Must-have:** Evidence shows correct progression through empty-market and
  later rolling-inventory rounds.
- [ ] **Must-have:** Evidence shows both popularity-information and
  no-popularity conditions.
- [ ] **Must-have:** Automated bots complete the experiment end to end.

## Notes

- Human feedback has been recorded; no numeric score has been provided yet.
