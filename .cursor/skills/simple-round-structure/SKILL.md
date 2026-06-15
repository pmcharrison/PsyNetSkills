---
name: simple-round-structure
description: Choose a static round structure for repeated PsyNet rounds with no cross-round state dependence.
authors: [eandrade-lotero]
---

# Choose a round structure

Use this skill when a PsyNet experiment describes repeated rounds, turns,
games, blocks, exchanges, or other participant actions that progress through a
sequence, and the state for a round does not depend on the state obtained after
the previous round is completed.

The goal is to keep static round designs simple by using `StaticNode`,
`StaticTrial`, `StaticTrialMaker`, explicit blocks, `choose_block_order`, or a
timeline loop when the round order and contents can be known before the
participant starts the sequence.

If the next round must be generated from the completed previous round, read
`state-dependent-round-structure/SKILL.md` instead.

## Required reads

- Read `psynet-experiment-implementation/SKILL.md` for the general experiment
  workflow and validation expectations.
- For live grouped interaction, also read
  `psynet-synchronous-experiments/SKILL.md` and
  `psynet-realtime-synchronous-experiments/SKILL.md` as appropriate.
- Inspect the closest PsyNet demos and the current trial-maker docs before
  coding.

## Classification checklist

Use a static repeated-trial structure when:

- each round is independent or has only participant-local carryover;
- the next round can be selected from a fixed manifest, block order, or loop;
- round state does not need to become a PsyNet node for later allocation;
- no downstream node must summarize completed trials to generate the next state;
- dashboard review does not need network, node, or chain tables to understand the
  experiment.

Do not use this skill as the owner when:

- the experiment state evolves from previous participant responses;
- `summarize_trials` should convert completed trial answers into the next round
  definition;
- the design is a chain, graph, Gibbs, MCMCP, create-and-rate, social
  transmission, or another networked paradigm.

## Implementation guidance

- Do not equate one visual page or one game round with one PsyNet `Trial`.
  A single trial may contain multiple browser states or multiple internal rounds
  when the trial answer records the completed session.
- Keep the implementation boring: use `StaticNode`, `StaticTrial`,
  `StaticTrialMaker`, explicit blocks, `choose_block_order`, or a timeline loop
  so visible round numbers match the actual trial order.
- Do not rely on `StaticTrialMaker`'s default block order when visible round
  numbers or stimulus order matter. Make the order explicit.
- For grouped trials, set `sync_group_type` on the trial maker when group members
  should follow the same node or trial allocation. Use barriers inside
  `Trial.show_trial` only for phase boundaries inside that trial.
- For live websocket sessions inside one trial, keep the static node definition
  as the source of session parameters and save the accepted event sequence or
  final summary in the trial answer.

## Validation

- Add bot or integration assertions for the chosen structure:
  - static repeated designs should prove the intended number and order of trials
    or rounds were completed;
- After local simulation or performance testing, inspect the dashboard/database:
  - static repeated designs should expose the expected trial and response data.
- For performance evidence, check trial-count metrics. A round-based experiment
  that should use PsyNet trials but reports zero completed trials is a structural
  warning even if participants reached the completion page.

## Common failures

- Do not store all round outcomes only in participant vars when the design needs
  PsyNet trial or node records.
- Do not add chain classes as a wrapper for static rounds. Use the static trial
  architecture unless completed trials must generate later round state.
- Do not let websocket or synchronization code hide the core PsyNet structure.
  Decide the static trial/node architecture first, then implement live
  interaction inside that boundary.
