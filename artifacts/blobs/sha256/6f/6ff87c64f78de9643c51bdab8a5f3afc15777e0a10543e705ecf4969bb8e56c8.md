# Replication memory simulation study

This folder contains a self-contained PsyNet experiment plus local simulation
and analysis scripts for the study-replication loop.

## Experiment

The PsyNet experiment is a static word-pair memory task. Participants see a cue
and choose the originally paired target from four alternatives: target,
semantic lure, recent-target lure, and neutral lure. Four trials are literal and
four include stronger interference.

## Simulated profiles

- `psynet_bot_rule`: the PsyNet bot-style rule-following profile.
- `scripted_noisy`: a stochastic inattentive profile.
- `mock_llm_memory_limited`: a prompt-style local mock LLM profile.
- `semantic_bias`: a semantic-lure biased profile.

The mock LLM profile is deterministic/local and does not call any real API.

## Commands

Run the experiment with PsyNet bots:

```bash
psynet test local
```

Create initial and revised local simulation exports:

```bash
python3 simulate_profiles.py --run-id initial --seed 577 --output-dir ../../evidence/exports/initial_data
python3 simulate_profiles.py --run-id revised --seed 578 --revised --output-dir ../../evidence/exports/revised_data
```

Analyze and compare the exports:

```bash
python3 analyze_exports.py \
  --initial-zip ../../evidence/exports/initial_data.zip \
  --revised-zip ../../evidence/exports/revised_data.zip \
  --output-dir ../../evidence/analysis
```
