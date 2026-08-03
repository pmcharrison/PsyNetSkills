---
title: Quorum personality and guessing game experiment
type: experiment implementation
difficulty: 6
authors: [eandrade-lotero]
---

Implement a PsyNet experiment that adapts the quorum example from PsyNet's
synchronization tutorial. Keep the tutorial's quorate main loop as the main
experiment once a sufficiently large group is present. Modify the
lobby/waiting-room experience so participants wait productively by completing a
two-stage personality and guessing-game task while the quorum forms.

Participants should first read clear instructions explaining the quorum
mechanism, the personality questions, the guessing game, how responses are
recorded, and how timeout or group-loss behavior is handled. Use PsyNet's
native synchronization tools rather than custom polling logic. In particular,
adapt the `SimpleGrouper` pattern from the quorum tutorial, including
`waiting_logic`, `join_existing_groups`, a minimum group size, and explicit
checks that participants only enter the main loop when the group is quorate.

The post-quorum main loop should remain the quorum tutorial's main loop: after
participants are released from the lobby, they should proceed through repeated
quorate-status iterations while the group remains quorate. Do not replace that
main loop with the personality or guessing tasks.

The lobby/waiting room should contain a two-stage productive waiting task with
up to 40 total lobby iterations or nodes:

- 10 personality iterations using the short Big Five personality items used by
  `PersonalityTrial` in the referenced ultimatum-game repository. Each prompt
  should ask participants how accurate a statement is for them, following the
  wording style of `PersonalityTrial`, for example "I see myself as someone who
  ...". Use the ten short-form items listed in `references/personality-items.md`.
- 30 guessing-game iterations. On each guessing iteration, define a hidden target
  number between 0 and 10 inclusive. Participants should make their guess with a
  PsyNet `SliderControl`, also bounded from 0 to 10 inclusive.

These 40 lobby iterations are a menu of productive waiting pages, not a required
precondition for entering the main experiment. Make it clear to participants
that they may be moved onward as soon as the quorum is obtained, even if they
have not finished all personality or guessing lobby pages.

For the personality lobby trials, use PsyNet's native `PushButtonControl`
instead of radio buttons or a custom Likert control. The response options should
implement a five-point accuracy scale from "Very inaccurate" to "Very
accurate". Save enough data to identify the personality item, item metadata
where relevant, the selected response, and the participant who answered it.

For the guessing-game lobby trials, participants should receive feedback after
each guess based on the absolute difference between their guess and the hidden
target:

- "Warmer" when the difference is exactly 1 coin.
- "A little warmer" when the difference is exactly 2 coins.
- "Cold" when the difference is greater than 2 coins.
- A clear success message when the participant guesses the target exactly.

The hidden target should not be shown before the guess is submitted. After the
guess, save the target, the guess, the absolute difference, the feedback label,
the node or round identifier, and the participant identifier. The implementation
should make the current iteration number and task type clear to participants.

Participants should not waste time while waiting for the quorum. If a participant
is waiting for enough other participants to be present, present waiting logic
based on the two-stage personality and guessing-game interface, as in the
tutorial's waiting-trial pattern. Waiting responses should be recorded as lobby
data and kept analytically separate from the quorate main-loop data. The lobby
sequence should tolerate interruption: once the quorum condition is met, PsyNet's
synchronization logic may release the participant from the current waiting loop
without requiring all 40 lobby pages to be completed.

All participant-facing pages should have appropriate time limits so that one
participant cannot indefinitely block the group. If a participant times out or
the group falls below quorum, the experiment should handle this gracefully using
PsyNet's synchronization and failure mechanisms, and should either return
remaining participants to productive waiting trials or end them with a clear
message.

The experiment should end with a completion page summarizing that the participant
finished the quorate main loop. If scores or bonuses are introduced for lobby
guessing-game pages, the instructions and completion page should state how they
are calculated and should not imply that unfinished lobby pages were required.

The submitted evidence should demonstrate that:

- Multiple participants can be grouped into a quorum and released into the main
  experiment only when the quorum condition is met.
- The post-quorum main loop remains the tutorial-style quorate loop rather than
  the personality or guessing tasks.
- Waiting participants complete two-stage personality and guessing-game lobby
  trials instead of idle pages.
- The 10 personality lobby nodes use `PushButtonControl` with five accuracy
  choices and store the expected item identifiers.
- The 30 guessing lobby nodes use `SliderControl`, hide the target until
  submission, and produce the correct feedback for exact guesses, difference 1,
  difference 2, and differences greater than 2.
- Participants can be released from the lobby when the quorum is obtained before
  all lobby personality or guessing pages are finished.
- If one participant leaves or fails while the group is quorate, the remaining
  participants encounter the intended recovery, waiting, or end-state behavior.
