---
title: Prisoner's dilemma experiment
type: experiment implementation
difficulty: 6
authors: [pmcharrison]
---

Implement a PsyNet experiment where participants play a repeated Prisoner's
Dilemma game and see the consequences of each choice.

The experiment should:

- Present at least six rounds of a Prisoner's Dilemma game.
- Let the participant choose either cooperate or defect on each round.
- Use a clearly described partner, which may be another participant or a
  simulated partner with a documented strategy.
- Apply this payoff matrix on every round:
  - both cooperate: 3 points each;
  - participant cooperates and partner defects: participant 0, partner 5;
  - participant defects and partner cooperates: participant 5, partner 0;
  - both defect: 1 point each.
- Show round-by-round feedback including both choices, the participant's payoff,
  and the participant's cumulative score.
- Save enough data to reconstruct each round, including the participant choice,
  partner choice, participant payoff, partner payoff, round number, and partner
  strategy or identifier.
- Include clear instructions before the task and a completion page that reports
  the participant's final score.
