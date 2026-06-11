---
title: LLM-assisted participation defense kit
type: experiment implementation
difficulty: 8
authors: [ww577]
---

Implement a PsyNet-native participant quality and AI-assistance review kit for
text-heavy experiments. The implementation should include a small runnable
PsyNet experiment, local simulated participant profiles, exported
PsyNet-format data, a transparent manual-review flagging script, and a report
explaining what each signal can and cannot establish.

The goal is to help researchers review participant quality in text-heavy
studies without overstating the evidential value of browser or response
telemetry. The kit should distinguish in-study signs of low effort or possible
AI assistance from platform-level fraud concerns that PsyNet cannot verify on
its own.

## Experiment design

Build a compact PsyNet experiment around a simple text-heavy task. For example,
participants might read short prompts, summarize short passages, explain their
reasoning for rating decisions, or answer brief open-response questions about
locally defined stimuli. The task content should be ethically neutral, small
enough to run locally, and designed only as a vehicle for demonstrating quality
review signals.

The participant flow should include:

1. an upfront instruction page that either prohibits AI assistance or asks
   participants to disclose any AI use;
2. several normal task trials with open-text responses;
3. at least one attention check and at least one comprehension check;
4. telemetry collection for timing, focus changes, paste events, and text
   production; and
5. an ECLAIR-style set of open-text probe questions or a clearly documented
   local approximation.

The AI-use instruction or disclosure component should be clear, participant
facing, and recorded in the exported data where feasible. It should not rely on
external survey platforms or paid recruitment services.

## Telemetry and review signals

Record enough local telemetry to support participant-level manual review. The
implementation should capture, at minimum:

- trial identifiers, stimulus metadata, participant identifiers, and simulated
  participant profile labels;
- normal task responses and open-text probe responses;
- attention-check and comprehension-check answers, including whether each
  answer matches the expected response;
- timing telemetry such as page load time, trial start time, submission time,
  and response latency;
- browser focus, blur, visibility-change, or tab-switch events where feasible;
- paste events, including counts and associated trial identifiers; and
- at least one keystroke or text-production signal where feasible, such as
  keydown counts, edit counts, inter-key latencies, or text growth over time.

Use PsyNet trial data, page data, participant variables, or exported structures
that remain close to PsyNet's normal data model. If some telemetry must be
mocked or normalized for local analysis, document the boundary between directly
recorded PsyNet data and derived or simulated fields.

## Threat taxonomy

Include a concise threat taxonomy in the implementation report. The taxonomy
should distinguish at least:

- attentive human-like participation;
- inattentive or low-effort participation;
- AI-assisted participation by an otherwise verified human participant;
- browser automation or browser-agent participation; and
- platform or account fraud, such as identity, payment, or recruitment-account
  abuse.

Explain which parts of the kit operate inside the PsyNet study and which
concerns require platform-level controls outside PsyNet. The implementation must
not imply that client-side telemetry, timing, or text-production signals prove
that a participant used an LLM, was automated, or committed platform fraud.

## Local simulation

Use local bots, simulated participants, and mock data only. Do not use real
Prolific, Cint, Qualtrics, AWS, production credentials, private participant
records, private datasets, or other production services.

Simulate multiple participant profiles so the review script has meaningful
examples to inspect. Include at least:

- an attentive human-like profile;
- an inattentive profile;
- a paste-heavy profile;
- a fast low-effort profile; and
- a mock LLM-assisted profile, browser-agent-like profile, or another clearly
  documented local approximation of AI-assisted participation.

The profile simulations should be transparent fixtures or scripts, not hidden
heuristics. They may be implemented as PsyNet bots, generated exports, local
mock participants, or a combination of these, provided the report explains how
each profile was produced and how closely the output matches PsyNet export
shape.

## Review script and outputs

Write a manual-review flagging script that reads the exported or simulated
PsyNet-format data and produces participant-level review output. The script
should use understandable rules such as failed checks, very short latencies,
high paste counts, missing focus telemetry, unusually sparse keystroke
telemetry, or generic open-text probe responses.

The output should show each participant, the observed signals, and whether the
participant should be flagged for manual review. The script must not
automatically reject participants and must not claim that telemetry proves AI
use. Use conservative language such as "flag for review", "review-worthy
signal", or "requires human inspection".

Write a report describing:

- the implemented PsyNet experiment and participant-facing flow;
- the AI-use instruction or disclosure component;
- the telemetry fields and how they are recorded or simulated;
- the simulated participant profiles and their intended behaviors;
- the flagging rules and review output;
- the distinction between platform-level defenses and PsyNet-native defenses;
  and
- what each signal can and cannot establish about participant quality,
  possible AI assistance, browser automation, or platform fraud.

## Evidence and provenance

Collect participant-facing evidence from a local run, preferably as a browser
video such as `participant.mp4`, showing the AI-use instruction or disclosure
page, at least one normal text-heavy task trial, at least one check, and at least
one open-text probe.

Include exported local PsyNet data or clearly documented simulated
PsyNet-format data, the review script output, and the report. Record
implementation provenance in `agent.json`, a concise event timeline in
`TIMELINE.md`, and reusable lessons in `LEARNINGS.md`.
