---
score: 3
---

# Evaluation

## Summary

The evaluator reported serious interaction issues in the participant flow and
requested a follow-up implementation pass. No numeric score was provided.

## Strengths

- The challenge direction remains useful, but the current implementation needs
  revisions before it should be treated as complete.

## Weaknesses

- A participant sometimes has to click a cell twice, or many more times, before
  the choice is registered and the next participant can play. The UI can show
  “Partner clicked; choose your cell”; after clicking it may return to
  “Connected” instead of advancing the turn.
- The evaluator saw local PostgreSQL connection-refused errors while using
  `psynet debug local`; this may have been caused by the evaluator's local disk
  space issue rather than by the experiment implementation.
- The implementation should move task/session parameters into node definitions,
  use a chain trial maker design, support configurable group sizes, improve
  turn-taking clarity, and update the UI/probability defaults.

## Criteria

- [ ] Participants are grouped into dyads with `SimpleGrouper`; the game is not a single-player simulation or a mock two-player display in one participant session.
- [ ] Each dyad plays one synchronous trial with 64 rounds, and both participants' round progression is coordinated within that trial.
- [ ] The interactive game uses PsyNet websocket functionality for real-time state exchange between the two participants.
- [ ] The pixel grid size is controlled by a global experiment variable and defaults to 8 by 8.
- [ ] The low and high Bernoulli signal probabilities are controlled by global experiment variables and default to 0.25 and 0.75.
- [ ] Each participant click samples and displays only that participant's own binary signal from the clicked cell's hidden probability.
- [ ] The hidden pattern of high-probability cells is defined and recorded well enough to evaluate whether participants could infer which cells have `p_ij > 0.5`.
- [ ] Each participant sees a live heatmap of the partner's click locations during the trial, positioned to the right of their own clickable grid.
- [ ] Partner rewards or signal outcomes are not shown in the UI, sent to the partner client, or recoverable from ordinary participant-facing state.
- [ ] Saved data are sufficient to reconstruct each participant's click sequence, sampled signals, hidden cell probabilities, and partner-click updates.
- [ ] The attempt includes clear participant instructions, a completion page, and evidence from two simultaneous participant sessions showing the heatmap update in real time.

## Notes

- Score and feedback should come from a human evaluator, captured
  conversationally when working with Cursor Cloud Agents.
- Implementation evidence collected: participant walkthrough video, performance-test JSON/log, dashboard monitor HTML, and exported local data zip.
- Requested repair items: node-defined session parameters, chain trial maker,
  configurable participant count, aggregate heatmap of other participants,
  named turn status, per-round checkmarks, border coordinates, timers, turn
  sound, click feedback color, positive-signal reward text, and low/high
  probabilities of 0.33/0.67.
- The requested repairs were recorded as a new follow-up attempt:
  `2026-06-09-19-01`.
