---
name: simple-round-structure
description: Decide whether a round-based PsyNet experiment should use a simple repeated-trial structure or explicit chain/node/trial-maker architecture.
authors: [eandrade-lotero]
---

# Choose a round structure

Use this skill when a PsyNet experiment describes repeated rounds, turns,
games, blocks, exchanges, or other participant actions that progress through a
sequence.

The goal is to decide whether the design is a simple repeated-trial structure,
or whether PsyNet should explicitly represent the sequence using nodes, trials,
and a trial maker such as `ChainNode`, `ChainTrial`, and `ChainTrialMaker`.

## Required reads

- Read `psynet-experiment-implementation/SKILL.md` for the general experiment
  workflow and validation expectations.
- For live grouped interaction, also read
  `psynet-synchronous-experiments/SKILL.md` and
  `psynet-realtime-synchronous-experiments/SKILL.md` as appropriate.
- Inspect the closest PsyNet demos and the current trial-maker docs before
  coding. For chain designs, read `~/PsyNet/docs/getting_started/chain_experiments.rst`.

## Classification checklist

Classify the round structure before implementing the timeline.

Use a simple repeated-trial structure when:

- each round is independent or has only participant-local carryover;
- the next round can be selected from a fixed manifest, block order, or loop;
- round state does not need to become a PsyNet node for later allocation;
- no downstream node must summarize completed trials to generate the next state;
- dashboard review does not need network, node, or chain tables to understand the
  experiment.

Use explicit PsyNet node/trial-maker architecture when:

- the experiment state evolves from previous participant responses;
- a round, game, or session should be attached to a PsyNet node for persistence,
  allocation, dashboard monitoring, or later analysis;
- multiple participants must receive the same node or trial allocation;
- `summarize_trials` should convert completed trial answers into the next
  definition or a node-level summary;
- the design is a chain, graph, Gibbs, MCMCP, create-and-rate, social
  transmission, or another networked paradigm;
- a specification or evaluator expects `Trial`, `TrialMaker`, `Node`, or chain
  records to appear in the dashboard/database.

## Implementation guidance

- Do not equate one visual page or one game round with one PsyNet `Trial`.
  A single trial may contain multiple browser states or multiple internal rounds
  when the trial answer records the completed session.
- Do not replace a needed `TrialMaker` with a hand-built sequence of
  `PageMaker` and `GroupBarrier` elements just because the task is round-based.
- For a simple repeated structure, keep the implementation boring: use a
  `StaticTrialMaker`, explicit blocks, `choose_block_order`, or a timeline loop
  so visible round numbers match the actual trial order.
- For chain architecture, define the node as the state PsyNet allocates, the
  trial as the participant-facing response unit, and the trial maker as the
  owner of allocation, quotas, network growth, and completion.
- For grouped trials, set `sync_group_type` on the trial maker when group members
  should follow the same node or trial allocation. Use barriers inside
  `Trial.show_trial` only for phase boundaries inside that trial.
- For live websocket sessions inside one trial, load session parameters from the
  trial's node definition and save the accepted event sequence or final summary
  in the trial answer.

## Validation

- Add bot or integration assertions for the chosen structure:
  - simple repeated designs should prove the intended number and order of trials
    or rounds were completed;
  - chain designs should prove completed trials are attached to the expected node
    class and `trial_maker_id`.
- After local simulation or performance testing, inspect the dashboard/database:
  - simple repeated designs should expose the expected trial and response data;
  - chain designs should expose the expected network, node, trial-maker state,
    and trial tables.
- For performance evidence, check trial-count metrics. A round-based experiment
  that should use PsyNet trials but reports zero completed trials is a structural
  warning even if participants reached the completion page.

## Common failures

- Do not store all round outcomes only in participant vars when the design needs
  PsyNet trial or node records.
- Do not add chain classes only as a wrapper if bot tests and dashboard data do
  not prove the generated trials are attached to the intended nodes.
- Do not treat `ChainNode` as a generic data container; use it when PsyNet needs
  a node state that can be allocated, summarized, or advanced.
- Do not let websocket or synchronization code hide the core PsyNet structure.
  Decide the trial/node architecture first, then implement live interaction
  inside that boundary.
