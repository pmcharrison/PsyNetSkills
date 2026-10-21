# Evaluation criteria

Use these criteria to assess completed attempts for the real-time synchronous
game challenge.

An attempt should pass only if it demonstrates all of the following:

- Participants are grouped into dyads with `SimpleGrouper`; the game is not a
  single-player simulation or a mock two-player display in one participant
  session.
- Each dyad plays one synchronous trial with 64 rounds, and both participants'
  round progression is coordinated within that trial.
- The interactive game uses PsyNet websocket functionality for real-time state
  exchange between the two participants. Polling, page reloads, or post-trial
  aggregation alone should not count as satisfying the websocket requirement.
- The pixel grid size is controlled by a global experiment variable and defaults
  to 8 by 8.
- The low and high Bernoulli signal probabilities are controlled by global
  experiment variables and default to 0.25 and 0.75.
- Each participant click samples and displays only that participant's own binary
  signal from the clicked cell's hidden probability.
- The hidden pattern of high-probability cells is defined and recorded well
  enough to evaluate whether participants could infer which cells have
  `p_ij > 0.5`.
- Each participant sees a live heatmap of the partner's click locations during
  the trial, positioned to the right of their own clickable grid.
- Partner rewards or signal outcomes are not shown in the UI, sent to the
  partner client, or recoverable from ordinary participant-facing state.
- Saved data are sufficient to reconstruct each participant's click sequence,
  sampled signals, hidden cell probabilities, and partner-click updates.
- The attempt includes clear participant instructions, a completion page, and
  evidence from two simultaneous participant sessions showing the heatmap update
  in real time.

Common reasons to fail an attempt:

- The implementation only stores clicks after a page submit or trial completion.
- The partner heatmap updates only after refreshing the page.
- The second player is represented by generated fake clicks rather than a real
  grouped participant.
- Partner signal outcomes are visible to the other participant or included in
  websocket payloads sent to the other participant's browser.
- The task is split into separate PsyNet trials in a way that prevents continuous
  real-time interaction within a single synchronous trial.
