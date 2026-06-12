---
name: process-dyadic-experiment-data
description: Convert PsyNet two-player round-based experiment exports into clean player-round analysis datasets.
authors: [eandrade-lotero]
---

# Process dyadic experiment data

Use this skill when a PsyNet experiment has two participants interacting across
rounds and the user needs exported or simulated data converted into a clean
analysis dataset.

The default clean layout is one row per experimental batch, dyad, round or node,
and player.

## Required reads

- Read `psynet-experiment-implementation/SKILL.md` for simulation, exported data,
  analysis-script, and report expectations.
- For grouped, barrier-based, or live two-player experiments, read
  `psynet-synchronous-experiments/SKILL.md`.
- For websocket or continuous live interaction, read
  `psynet-realtime-synchronous-experiments/SKILL.md`; it owns the distinction
  between raw events, reconstructed state, and participant-specific deliveries.

## Workflow

1. Identify the source tables or files from the PsyNet export or simulation.
   Record which source is authoritative for accepted actions, round state, role
   assignment, scores, timeouts, and failed or incomplete trials.
2. Reconstruct stable identifiers:
   - experimental batch;
   - dyad or group ID;
   - network, node, trial, or session ID;
   - round number;
   - participant ID;
   - player index, role, or side within the dyad;
   - partner participant ID.
3. Define the round state before flattening data. List the variables that
   determine the state, such as shared resources, private resources, visible
   signals, hidden attributes, current turn, previous actions, timers, and
   cumulative outcomes.
4. Extract each participant's action for each round. Include action values and
   any analysis-relevant metadata such as submission time, acceptance time,
   timeout status, validity, revision count, duplicate submission status, or
   out-of-turn rejection.
5. Extract scores at the right level:
   - player-round score;
   - partner score;
   - dyad or group score;
   - cumulative score;
   - bonus-relevant score;
   - score components when they are needed to audit the rule.
6. Build the canonical player-round table with one row per batch, dyad, round,
   and participant. Prefer explicit columns for commonly analyzed state and
   action variables. Keep nested `state_json`, `action_json`, or raw event IDs
   only when they remain useful for auditing.
7. Show a partial reconstructed dataset before finalizing. Present a small
   representative preview across multiple dyads and rounds, plus the proposed
   data dictionary. Ask the user whether they want schema tweaks, such as adding
   variables, excluding irrelevant columns, renaming fields, changing player and
   partner representations, splitting nested state into explicit columns, or
   adding derived analysis variables.
8. Write final outputs after review:
   - `clean_round_player.csv` or `.parquet`;
   - a data dictionary describing every column;
   - optionally `round_level.csv` with one row per dyad-round for aggregate
     analyses;
   - a short processing report naming source files, assumptions, exclusions, and
     validation results.

## Validation checklist

- Each complete dyad-round has exactly two player rows.
- Each participant has at most one clean row per dyad-round-player role.
- Player order is stable across rounds, or role changes are explicitly recorded.
- Partner fields are symmetric and point to the other participant in the dyad.
- Round state can be reconstructed deterministically from the recorded sources.
- Clean action and score values match the authoritative raw events or trial
  answers.
- Timeouts, invalid actions, dropouts, skipped rounds, failed trials, and
  one-sided responses are represented according to a documented missingness
  policy.
- The clean table preserves enough IDs to trace any row back to the source
  event, trial, node, or export row.

## Common failures

- Do not silently treat browser-local state as authoritative when server events
  or accepted trial answers exist.
- Do not collapse dyad-round data to one row per round when the requested
  analysis needs one row per player.
- Do not hide role assignment or player ordering inside column names that cannot
  be compared across rounds.
- Do not discard raw event IDs, trial IDs, or node IDs before the clean dataset
  has passed audit checks.
- Do not finalize the schema before showing the user a partial reconstruction
  and asking whether irrelevant information should be removed or missing
  variables should be added.
