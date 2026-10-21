---
title: Adaptive real-time Prisoner's Dilemma
type: experiment implementation
difficulty: 9
authors: [lucasgautheron]
---

Implement a PsyNet experiment in which pairs of participants play a real-time,
synchronous, iterated Prisoner's Dilemma game. The experiment should compare two
treatments: one in which dyads play without communication, and one in which dyads
can chat while the game is underway. Treatment assignment should support both a
static mode and an adaptive mode controlled by one global variable in
`experiment.py`.

## Procedure

Participants should first read concise instructions explaining the two available
actions, the payoff logic, the communication treatment, and how their points map
onto real bonus payments. After any necessary consent and instruction checks,
participants should wait until they can be paired with another active participant.
Use PsyNet groupers and barriers to form dyads and to ensure that both members of
the dyad enter the game together.

Each dyad should be assigned to exactly one treatment before its game begins.
Dyads in the no-communication treatment play the game without chat. Dyads in the
communication treatment see a chat room to the right of the main game interface
and can exchange messages during the game. A dyad should play one sequence only;
participants should not be regrouped for additional sequences.

The game should contain 10 scored iterations. On each iteration, both players
choose simultaneously between two clearly labelled actions. Make the action
labels easy to change globally, but render them in the participant interface as
buttons of the form **Play "XXX"** and **Play "YYY"**. The interface should show a
visible countdown for the current decision window and a visible indication of how
much of the 10-iteration sequence remains. Play an audible cue when a participant
needs to make a choice.

After both players have submitted their choices, both participants should receive
immediate feedback showing what each player chose, how many points each player
earned on that iteration, and each player's cumulative points. Participants
should then advance synchronously to the next iteration until all 10 iterations
are complete.

## Adaptive treatment assignment

Provide a single global experiment variable in `experiment.py` that switches
between:

- **Static mode**, in which treatment assignment uses a fixed experiment-level
  rule such as equal random assignment across dyads.
- **Adaptive mode**, in which treatment assignment uses an active-inference
  multi-armed bandit approach to decide whether the next dyad should receive the
  communication or no-communication treatment.

The adaptive objective is to maximize the probability of cooperation. Define the
outcome measure before implementation begins, for example the proportion of
cooperative choices across the dyad's 10 iterations or cooperation in the final
iterations. Save enough model state and assignment metadata to reconstruct why
each dyad received its treatment, including the experiment mode, the candidate
treatments, prior settings, posterior or belief updates, observed cooperation
outcomes, and the random seed or stochastic choices used by the assignment
algorithm.

Use the active-inference multi-armed bandit implementation from the
`active-inference-with-people` repository as the main methodological reference,
adapting it to dyad-level treatment assignment rather than individual stimulus
selection.

## Interface

Build a sober, polished JavaScript interface suitable for real-time dyadic play.
Participants should always be able to understand the payoff consequences of
their next choice. Present the payoff structure in natural language, not only as
a mathematical table. For example, explain what happens if both players choose
one action, if both choose the other action, and if the two players choose
different actions. It is fine to include a compact visual summary as long as the
plain-language explanation is primary.

The main game area should show:

- The participant's two action buttons.
- The current iteration number out of 10.
- A timer for the current decision window.
- A timer or progress indicator for the remaining game sequence.
- The participant's own cumulative points and estimated bonus.
- Feedback from the previous iteration once it is available.

When communication is enabled, show the chat room to the right of the main game
area. The chat should be clearly unavailable or absent in the no-communication
treatment. Chat messages should not block simultaneous play, timers, or choice
submission.

## Data and bonuses

Convert points into real participant bonuses using a clear, documented exchange
rate. Participants should be told before the game how bonuses are computed and
should see their final bonus at the end of the sequence.

Record enough data to reconstruct the full dyadic interaction:

- Dyad membership, barrier timing, treatment assignment, and experiment mode.
- Every iteration's decision-window timing, choice submissions, missing or late
  responses, and feedback timing.
- Both players' choices, iteration payoffs, cumulative points, and final bonuses.
- Chat transcripts and message timestamps for communication dyads.
- Websocket events needed to audit real-time synchronization.
- Adaptive-model inputs, outputs, and updates for each dyad assignment.

## Implementation requirements

- Use PsyNet's synchronous grouping and barrier patterns to form and release
  dyads.
- Use websockets for real-time game state, simultaneous decisions, timers, chat
  updates, and feedback.
- Keep treatment assignment at the dyad level, before the dyad starts its single
  10-iteration sequence.
- Keep the static/adaptive mode switch centralized in `experiment.py`.
- Do not require production credentials or external services beyond local PsyNet
  development defaults.
- Include automated bots or simulations that can exercise both treatments and
  both experiment modes locally.

## Evidence

Submitted evidence should demonstrate:

- Two participants being grouped into a dyad and released through the game
  barriers together.
- A dyad completing all 10 real-time simultaneous iterations.
- Choice buttons, timers, sounds, feedback, cumulative points, and final bonuses
  working as specified.
- The communication treatment showing a functional chat room while the
  no-communication treatment does not.
- Static mode assigning treatments according to the fixed rule.
- Adaptive mode updating treatment-assignment beliefs from observed cooperation
  outcomes and using those beliefs for later dyads.
