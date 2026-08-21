---
title: Ultimatum game experiment
type: experiment implementation
difficulty: 6
authors: [eandrade-lotero]
---

Implement a PsyNet experiment in which two participants play a repeated
Ultimatum game synchronously.

Participants should first read clear instructions explaining the proposer and
responder roles, the 10-coin endowment, how proposals are made, how accept and
reject decisions affect payoffs, how timeouts are handled, and how the final
score is calculated. The instructions should make clear that roles can change
from round to round.

Each pair of participants should complete at least 10 scored rounds together.
At the beginning of every round, the experiment should randomly assign one
participant to be the proposer and the other participant to be the responder.
The proposer receives an endowment of 10 coins for that round and chooses how
many coins, from 0 to 10 inclusive, to offer to the responder.

The responder should wait until the proposal is available, then decide whether
to accept or reject it. If the responder accepts, the responder earns the
offered number of coins and the proposer earns the remaining coins from the
10-coin endowment. If the responder rejects, both participants earn 0 coins for
that round. After each counted round, both participants should receive feedback
showing their role, the proposal, the responder's decision, the coins earned by
each participant in that round, and their own cumulative score.

Use WebSockets to manage the real-time interaction between the two participants
during each round. The implementation should use live updates to notify the
responder when the proposal has been submitted, to notify the proposer when the
responder has accepted or rejected the proposal, and to keep both browsers in
sync during waiting and feedback states.

All pages should be timed so that neither participant can delay the pair
indefinitely. This includes instructions, proposer decisions, responder waiting,
responder decisions, feedback, and completion pages where relevant. If either
participant times out during the proposer or responder decision process, the
round should not count toward either participant's accumulated score, and both
participants should receive clear feedback explaining that the round was skipped
because of a timeout. Skipped rounds should not reduce the required number of
successfully counted rounds unless the implementation explicitly documents a
fixed-round design and clearly reports which rounds were skipped.

The experiment should end with a completion page that summarizes the
participant's total score, confirms that the task is complete, and gives a
short explanation of how their score was accumulated.

The submitted evidence should demonstrate that two participants can be grouped
together, roles are randomized across rounds, proposals and accept/reject
decisions synchronize correctly between the two browsers via WebSockets,
accepted and rejected proposals produce the correct payoffs, timeout behavior
prevents a stalled round from contributing to accumulated scores, and both
participants reach the completion page.
