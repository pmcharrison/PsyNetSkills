# Simulated participant study replication loop

## Introduction

This attempt validates a local PsyNet study-replication workflow using simulated
participants. The target study is a word-pair memory experiment with literal and
interference trials. The workflow tests whether simulated profiles expose
instruction or export problems before a human-subject study is considered.

## Methods

The PsyNet experiment in `code/replication_memory/` presents eight static
memory trials. Each trial asks for the target word originally paired with a cue.
Alternatives include the true target, a semantic lure, a recent-target lure, and
a neutral lure. The local simulator writes PsyNet-style exports containing
participant rows, trial rows, event rows, run metadata, profile metadata,
conditions, responses, answer roles, and response timing.

The preregistration predicted high accuracy for a rule-following PsyNet bot
profile, lower and slower performance for a noisy script, recent-lure errors for
a prompt-style mock LLM with limited ordered memory, and semantic-lure errors
for a semantic-bias profile.

## Simulated participants

Four profiles were run with three participants each. `psynet_bot_rule` represents
PsyNet bot-style correct-answer behavior. `scripted_noisy` stochastically guesses
on some trials. `mock_llm_memory_limited` receives a prompt-like task
representation and confuses recent targets with correct targets. `semantic_bias`
overweights semantically related choices. No real LLM or external API is used.

## Results

The initial run produced 12 participants and 96 trials. The PsyNet bot profile
was at ceiling in both conditions. The mock LLM profile showed the expected
interference failure, with 0.167 interference accuracy and 10 recent-lure
choices. The semantic-bias profile made 10 semantic-lure choices in each
condition. The noisy profile was lower than the bot profile and had the highest
median response time.

## Revision

The revision clarified the prompt-style simulator instruction by warning that
recent words from other pairs can be traps. This was chosen because the initial
analysis showed a profile-specific recent-lure failure while the core experiment
and export metadata were already traceable.

## Revised results

The revised run again produced 12 participants and 96 trials. Mock LLM
interference accuracy improved from 0.167 to 0.750, and recent-lure choices
dropped from 10 to 3. The PsyNet bot profile stayed at ceiling, and the
semantic-bias profile continued to show semantic-lure errors, preserving
meaningful profile differences.

## Limitations

These simulated data validate the local experiment, export, and analysis
workflow; they are not evidence about real people. The mock LLM profile is a
local deterministic script rather than a production model, by design. A future
human study would still need real consent, recruitment, counterbalancing review,
and human behavioral validation.
