---
title: Common pool resource management experiment
type: experiment implementation
difficulty: 6
authors: [eandrade-lotero]
---

Implement a PsyNet experiment in which participants manage a common pool
resource in synchronous groups of three.

Participants should first read clear instructions explaining the coin endowment,
the contribution decision, the common pool growth rule, and how earnings are
updated across rounds. Each participant in a group should begin with the same
clearly stated number of coins.

In each round, all three participants should simultaneously choose how many of
their currently available coins to invest in the common pool. Once all three
participants have made their decisions, the experiment should increase the total
common pool contribution by 10% and then distribute the resulting amount equally
among the three participants. Participants' coin balances should update after
each round according to their own contribution and their equal share of the
expanded pool.

The experiment should include at least 10 scored rounds. After each round,
participants should see feedback that makes the outcome understandable,
including their own contribution, the total group contribution, the 10% increase,
their equal share of the pool, and their updated coin balance. The interface
should make it clear which round participants are completing and how many rounds
remain.

All pages should be timed so that participants cannot delay the group
indefinitely. If a participant times out on a contribution page, the experiment
should automatically record the maximum allowable contribution for that
participant in that round. Instruction, waiting, feedback, and completion pages
should also use appropriate time limits or automatic progression where relevant.

The experiment should end with a completion page that summarizes the
participant's final coin balance and confirms that the task is complete.

The submitted evidence should demonstrate that three participants can be grouped
together, complete the synchronous contribution rounds, receive correctly
calculated common-pool feedback, and finish on the completion page. The evidence
should also show or otherwise document the timeout behavior for at least one
contribution decision.
