---
title: Real-time synchronous game experiment
type: experiment implementation
difficulty: 5
authors: [lucasgautheron]
---

Implement a PsyNet experiment that demonstrates a real-time synchronous game
played by pairs of participants using websockets.

The experiment should:

- Group participants into dyads using `SimpleGrouper`.
- Let each dyad play a single synchronous trial containing 64 rounds.
- Show each participant a clickable pixel grid. The grid size should be
  controlled by a global experiment variable and default to 8 by 8.
- On every round, have each participant click one grid cell `(i, j)`.
- After each click, give that participant a random binary signal sampled from
  `Bernoulli(p_ij)`, where each cell's hidden probability `p_ij` is either low
  or high.
- Make the low and high signal probabilities adjustable via global experiment
  variables, defaulting to 0.25 and 0.75.
- Define a hidden cell pattern for each dyad or game, where the participant's
  goal is to infer which cells have `p_ij > 0.5`.
- Show each participant their own grid and, to its right, a heatmap of the other
  participant's clicks.
- Do not show a participant the other participant's reward or signal outcomes.
- Use websockets during the trial to synchronize participant state and share
  each participant's click attempts with their partner in real time.
- Save enough data to reconstruct each participant's click sequence, sampled
  signals, hidden cell probabilities, and received partner-click updates.
- Include clear participant instructions and a completion page.

The submitted evidence should demonstrate that two participants can play the
game together, that partner click heatmaps update during the synchronous trial,
and that hidden rewards remain private.
