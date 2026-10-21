---
title: Real-time synchronous game experiment
type: experiment implementation
difficulty: 5
authors: [lucasgautheron]
---

Implement a PsyNet experiment that demonstrates a real-time synchronous game
played by groups of participants using websockets.

The experiment should:

- Group participants using `SimpleGrouper`, with the group size controlled by a
  global experiment variable and defaulting to 2 participants. A trial maker
  (for now static) assigns trials to these groups.
- Let each group play a single synchronous trial containing 64 rounds.
- Show each participant a clickable pixel grid. The grid size should be
  controlled by a global experiment variable and default to 8 by 8.
- On every round, have each participant click one grid cell `(i, j)` when it is
  their turn. The turn order should be synchronized across the group.
- Define a hidden cell pattern for each group or game, where the participant's
  goal is to infer which cells have `p_ij > 0.5`.
- After each click, give that participant a random binary reward `y~Bernoulli(p_ij)`,
where each cell's hidden probability `p_ij` is either low or high.
- Make the low and high signal probabilities adjustable via global experiment
  variables, defaulting to 0.33 and 0.67.
- Show each participant their own grid and, to its right, a heatmap aggregating
  all other participants' clicks.
- When the reward is y=1, give participants $+0.01, and let the color of the cell be momentarily green while indicating the bonus; otherwise, give no financial reward, and let the color of the cell be momentarily red.
- Do not show a participant the other participants' reward or signal outcomes.
- Use websockets during the trial to synchronize participant state and share
  each participant's click attempts with the rest of the group in real time.
- Show timers indicating how much time remains to play, including a visible
  countdown for the current turn or response window.
- Clearly indicate whose turn it is in the UI, play a sound when it becomes the
  current participant's turn, and prevent out-of-turn clicks from being
  submitted.
- Display randomly generated participant names that remain consistent throughout
  the trial, marking the current participant's own name with "(you)".
- Within each round, show a group status list with checkmarks for participants
  who have already finished their turn and a clear marker for the participant
  who is next.
- Save enough data to reconstruct each participant's click sequence, sampled
  signals, hidden cell probabilities, received group-click updates, turn order,
  timing events, and participant display names.
- Include clear participant instructions and a completion page.

The submitted evidence should demonstrate that multiple participants can play
the game together, that aggregate heatmaps update during the synchronous trial,
that turn-taking, timers, sounds, names, and within-round completion checkmarks
work as specified, and that hidden rewards remain private.

The implementation should be easy to adapt if the interface or nature of the
task changes, or if chain trial makers are used rather than static trial makers.
