---
name: state-dependent-round-structure
description: Choose PsyNet chain/node architecture when each round depends on state produced by the previous completed round.
authors: [eandrade-lotero]
---

# Choose a state-dependent round structure

Use this skill when a PsyNet experiment describes repeated rounds, turns,
games, blocks, exchanges, or other participant actions where the state of one
round depends on the state obtained after the previous round is completed.

The goal is to represent the evolving state explicitly with PsyNet nodes,
trials, and a trial maker such as `ChainNode`, `ChainTrial`, and
`ChainTrialMaker`.

If all rounds are independent, participant-local only, or drawn from a fixed
manifest before the sequence begins, read `simple-round-structure/SKILL.md`
instead.

## Required reads

- Read `psynet-experiment-implementation/SKILL.md` for the general experiment
  workflow and validation expectations.
- Read `~/PsyNet/docs/getting_started/chain_experiments.rst` and inspect the
  closest PsyNet chain, graph, Gibbs, MCMCP, or create-and-rate demo before
  coding.
- When a specification says each visible round, game, or iteration should map to
  a chain node, read `references/chain-structure-integrity.md` before testing or
  reviewing the experiment.
- For grouped allocation or barriers, also read
  `psynet-synchronous-experiments/SKILL.md`.
- For live websocket interaction inside a trial, also read
  `psynet-realtime-synchronous-experiments/SKILL.md`.

## Classification checklist

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

- Define the node as the state PsyNet allocates, the trial as the
  participant-facing response unit, and the trial maker as the owner of
  allocation, quotas, network growth, and completion.
- Implement `summarize_trials` when completed trial answers must produce the next
  node definition, a node-level summary, or downstream allocation state.
- Do not replace a needed `TrialMaker` with a hand-built sequence of
  `PageMaker` and `GroupBarrier` elements just because the task is round-based.
- Do not equate one visual page or one game round with one PsyNet `Trial`. A
  single trial may contain multiple browser states or multiple internal rounds
  when the trial answer records the completed session.
- For grouped trials, set `sync_group_type` on the trial maker when group
  members should follow the same node or trial allocation. Use barriers inside
  `Trial.show_trial` only for phase boundaries inside that trial.
- For live websocket sessions inside one trial, load session parameters from the
  trial's node definition and save the accepted event sequence or final summary
  in the trial answer so `summarize_trials` has the data it needs.

## Validation

- Add bot or integration assertions proving completed trials are attached to the
  expected node class and `trial_maker_id`.
- Assert that the finalized answer data required for `summarize_trials` is
  present and generates the expected next node or node summary.
- For designs where each visible round should be a `ChainNode`, run the
  `references/chain-structure-integrity.md` audit with bots. Assert the expected
  number of distinct `trial.node_id` values, not just the number of raw node
  table rows.
- After local simulation or performance testing, inspect the dashboard/database
  for the expected network, node, trial-maker state, and trial tables.
- For performance evidence, check trial-count metrics. A round-based experiment
  that should use PsyNet trials but reports zero completed trials is a
  structural warning even if participants reached the completion page.

## Common failures

- Do not store all round outcomes only in participant vars when the design needs
  PsyNet trial or node records.
- Do not add chain classes only as a wrapper if bot tests and dashboard data do
  not prove the generated trials are attached to the intended nodes.
- Do not hide many visible rounds inside one `ChainTrial` when the spec expects
  downstream chain state per round. In that case, participant answers may report
  all rounds completed while PsyNet only stores one trial-attached node.
- Do not treat `ChainNode` as a generic data container; use it when PsyNet needs
  a node state that can be allocated, summarized, or advanced.
- Do not let websocket or synchronization code hide the core PsyNet structure.
  Decide the trial/node architecture first, then implement live interaction
  inside that boundary.
