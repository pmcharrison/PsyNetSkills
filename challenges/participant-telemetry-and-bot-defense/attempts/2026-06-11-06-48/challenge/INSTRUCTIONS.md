---
title: Participant telemetry and bot defense
type: experiment implementation
difficulty: 7
authors: [williambotticelli-wells]
---

Implement a small PsyNet experiment that records participant telemetry useful
for reviewing low-quality, bot-like, or LLM-assisted participation. The study
should run locally with PsyNet bots or simulated participants and should produce
exported or simulated PsyNet-format data for analysis.

## Research prompt

Design a brief task in which participants complete a normal sequence of simple
judgment trials. For example, participants might rate short statements, choose
between options, or classify small text or image-like stimuli. The task content
should be compact, locally defined, and ethically neutral; it is only a vehicle
for demonstrating telemetry collection and review.

The participant flow should include:

1. a concise introduction explaining the task;
2. several normal task trials with clear participant-facing instructions;
3. at least one attention or comprehension check embedded in the flow; and
4. a closing page.

The experiment should also include response-consistency opportunities, such as
repeated, reversed, or closely related items where a participant's answers can
be compared for coarse consistency. These checks should be suitable for local
simulation and should not depend on paid recruitment, production credentials, or
external services.

## Telemetry requirements

Record enough local data to support participant-level review. The implementation
should capture, at minimum:

- trial identifiers, stimulus metadata, and participant identifiers;
- participant responses on normal task trials;
- attention or comprehension check responses and whether they match the expected
  answer;
- timing telemetry such as page load or trial start time, response submission
  time, and response latency;
- data needed to compute response-consistency summaries across paired or
  repeated items; and
- metadata distinguishing local bot or simulated participant profiles from any
  mock human-like profiles used in the demonstration.

Store the telemetry in PsyNet trial data or exported data structures in a way
that a reviewer can inspect. If a local PsyNet export requires light
normalization before analysis, document the normalization and keep the simulated
or normalized file close to PsyNet's exported shape.

## Local simulation

Run the experiment locally with PsyNet bots or simulated participants only. Do
not use real Prolific, Cint, AWS, paid recruitment, production credentials, or
other production services.

Include several mock participant profiles that make the analysis meaningful. At
least one profile should behave plausibly, while other profiles should show
review-worthy patterns such as extremely fast responses, failed attention or
comprehension checks, repeated identical responses, inconsistent answers to
paired items, or missing telemetry. These profiles are for local testing only and
should not be presented as validated models of real human or AI behavior.

## Analysis and report

Write a transparent analysis or scoring script that reads the exported or
simulated PsyNet-format data and produces participant-level flags for suspicious
patterns. The script should use understandable rules, such as latency thresholds,
attention-check failure, low response variance, missing telemetry, or
inconsistency across paired items. It should output a concise table or structured
file showing each participant, the signals observed, and the resulting review
flag.

The scoring system must be conservative. It may identify participants for
manual review, but it must not automatically reject real participants and must
not claim that telemetry proves a participant is a bot, an AI system, or an
LLM-assisted respondent.

Write a short report describing:

- the implemented task and telemetry fields;
- how the local bots or simulated participants were generated;
- how the exported or simulated PsyNet-format data was analyzed;
- which participant profiles were flagged and why; and
- what each telemetry signal can and cannot establish about participant quality,
  bot-like behavior, or possible LLM assistance.

## Evidence and provenance

Collect participant-facing evidence from the local run, preferably as a browser
video such as `participant.mp4`, showing the implemented task flow including at
least one normal trial and one attention or comprehension check.

Include exported local PsyNet data or clearly documented simulated
PsyNet-format data, the scoring output, and the analysis report. Record
implementation provenance in `agent.json`, a concise event timeline in
`TIMELINE.md`, and reusable lessons in `LEARNINGS.md`.
