---
title: Simulated participant study replication loop
type: experiment implementation
difficulty: 9
authors: [ww577]
---

Create a local PsyNet study-replication workflow that uses simulated participants
to stress-test a nontrivial experiment, compares the simulated data against
preregistered qualitative expectations, revises the study or simulation once,
and documents the outcome in a short paper-style report.

## Study starting point

Choose or implement a nontrivial runnable PsyNet experiment as the target study.
The starting point may come from an existing PsyNetSkills challenge, a PsyNet
demo in `~/PsyNet/demos/`, or another local public/demo asset that can be used
without private data or production credentials. The chosen study should have
enough structure to make simulation informative, such as multiple trials,
conditions, adaptive behavior, memory, social interaction, audio or visual
stimuli, or a meaningful scoring rule. Do not use a one-page toy experiment as
the target.

If you adapt an existing challenge or demo, keep the scientific task recognizable
and document what you changed. If you implement a new experiment, keep it compact
enough to run locally but rich enough that different simulated participant
profiles could plausibly behave differently.

## Preregistered qualitative expectations

Before inspecting simulated results, write a short preregistration note. The
note should describe:

- the target experiment and why it is suitable for simulation;
- the participant profiles you plan to run;
- the qualitative response patterns you expect from each profile;
- the failure modes you expect simulated participants to reveal;
- which results would make you revise the study design, instructions, stimuli,
  bot behavior, or simulation strategy.

These expectations are not a statistical preregistration for a real study. They
are a local validation contract for evaluating whether the simulated workflow is
behaving coherently.

## Simulated participant profiles

Run multiple local simulated participant profiles. Include PsyNet bots and at
least one additional mock LLM-style or scripted response profile. The mock
LLM-style profile may be a deterministic or stochastic script that receives a
prompt-like representation of the task and returns responses in the same format
as a participant. It must not require real LLM API access.

Profiles should be meaningfully distinct. For example, they might include an
attentive rule-following participant, a noisy or inattentive participant, a
biased participant, a profile with memory limitations, or a profile that
misinterprets a key instruction. Record enough metadata to connect each exported
response to the simulated profile that produced it.

## Initial local run and export

Run the experiment locally with the simulated participant profiles. Use only
local PsyNet, local databases, and local or demo assets. Do not use real
recruitment, AWS, Prolific, Cint, production credentials, private data, or
private stimuli.

Export the resulting PsyNet-format data from the initial run. Preserve the raw
export or a clearly documented PsyNet-format export artifact, and include enough
metadata for a reviewer to identify participants, profiles, trials, conditions,
responses, and run timing.

## Analysis

Write a richer analysis notebook or script that runs on the exported data. The
analysis should go beyond counting rows. It should compare simulated participant
profiles, summarize expected condition-level or trial-level patterns, flag
profile-specific anomalies, and explicitly compare observed simulated results
with the preregistered qualitative expectations.

The analysis may use descriptive statistics, plots, tables, trace summaries, or
model-free checks that fit the chosen experiment. It should be reproducible from
the committed or archived export artifacts.

## Revision and rerun

Based on the initial run and analysis, revise either the study design or the
simulation strategy once. The revision might clarify instructions, adjust
stimuli, fix data logging, improve a bot response rule, add a profile metadata
field, or change how a mock LLM-style profile interprets the task. Explain why
the revision addresses a concrete failure mode observed in the first run.

Rerun the experiment locally after the revision, export the revised
PsyNet-format data, and rerun the analysis. Compare the revised results against
both the initial results and the preregistered expectations.

## Report

Write a short paper-style report describing the full loop. The report should
include concise sections such as Introduction, Methods, Simulated Participants,
Results, Revision, and Limitations. It should distinguish workflow validation
from human-subject evidence: simulated participant data may demonstrate that the
experiment, export, and analysis pipeline work, but it must not be presented as
evidence about real people.

## Deliverables

Include the following materials in the attempt:

- runnable PsyNet experiment code or a clearly documented adapted demo/challenge;
- preregistered qualitative expectations written before inspecting simulated
  results;
- configuration or scripts for each simulated participant profile;
- evidence of the initial local simulated run;
- PsyNet-format exported data from the initial run;
- analysis notebook or script and its outputs for the initial run;
- a documented revision to the study design or simulation strategy;
- evidence of the revised local simulated rerun;
- PsyNet-format exported data from the revised rerun;
- updated analysis comparing initial and revised results;
- a short paper-style report;
- implementation provenance in `agent.json`, a concise event timeline in
  `TIMELINE.md`, and reusable lessons in `LEARNINGS.md`.
