---
title: Apply participant quality telemetry skill
type: experiment implementation
difficulty: 7
authors: [williambotticelli-wells]
---

Use the `psynet-participant-quality-telemetry` skill to add participant-quality
telemetry and conservative manual-review outputs to a small text-heavy PsyNet
experiment. The implementation may adapt an existing local-only demo or create a
compact new experiment, but it must run locally in PsyNet and must not depend on
paid recruitment, production services, private participant data, or real service
credentials.

The goal is to demonstrate how a text-heavy study can collect interpretable
quality-review signals while avoiding overclaims about what those signals prove.
The finished attempt should include a runnable PsyNet experiment, simulated
participant profiles, exported PsyNet-format data, a transparent manual-review
flagging script, participant-facing evidence, and a short report.

## Experiment design

Build or adapt a brief text-heavy PsyNet experiment. For example, participants
might read short prompts and produce written explanations, summaries, or
justifications for simple ratings. The task content should be locally defined,
ethically neutral, and small enough to exercise the telemetry pipeline during a
local run.

The participant flow should include:

1. a concise introduction explaining the text task;
2. several normal open-text trials;
3. at least one attention or comprehension check; and
4. a closing page.

Participant-facing instructions should make the task requirements clear without
threatening automatic rejection. If the experiment mentions AI assistance, it
should use conservative wording such as disclosure, research integrity, or
manual review rather than claiming that the study can detect AI use with
certainty.

## Telemetry requirements

Use the `psynet-participant-quality-telemetry` skill as the implementation
guide. Record enough local telemetry to support participant-level manual review,
including at minimum:

- trial identifiers, stimulus metadata, participant identifiers, and simulated
  participant profile labels;
- normal task responses and attention or comprehension check responses;
- timing telemetry such as trial start time, submission time, and response
  latency;
- paste, focus, blur, visibility-change, or tab-switch telemetry where feasible;
  and
- at least one text-production signal such as keydown counts, edit counts,
  first-key latency, inter-key latency, or text growth over time.

Store the telemetry in PsyNet trial data, page data, participant variables, or
exported structures that remain close to PsyNet's normal data model. If a signal
is simulated or normalized after export, document that boundary clearly so a
reviewer can distinguish directly recorded telemetry from derived test data.

## Local simulation

Use local bots, scripted fixtures, or simulated participants only. Do not use
real recruitment, Prolific, Cint, Qualtrics, AWS, production credentials,
private data, or external fraud-detection services.

Simulate multiple participant profiles so the review outputs are meaningful.
Include at least one plausible profile and at least one suspicious profile. The
suspicious examples may show patterns such as very short latencies, failed
attention or comprehension checks, heavy paste activity, missing focus
telemetry, sparse keydown telemetry, or unusually generic text responses.

The simulated profiles should be transparent and reproducible. They may be
implemented as PsyNet bots, local export fixtures, or post-run data-generation
scripts, provided the attempt explains how each profile was produced and how
closely the output matches PsyNet export shape.

## Export, review script, and report

Export local PsyNet-format data, or provide clearly documented simulated data
that follows PsyNet's exported structure closely enough for a reviewer to inspect
participant-level trial records. Include the commands or scripts needed to
reproduce the export or generated fixture.

Write a transparent manual-review flagging script that reads the exported or
simulated PsyNet-format data and produces participant-level review output. The
script should use understandable rules such as failed checks, very fast
responses, high paste counts, focus loss, missing telemetry, sparse keydown
counts, or short first-key latencies. The output should show each participant,
the signals observed, and whether the participant should be flagged for manual
review.

The flagging logic must be conservative. It must not automatically reject
participants and must not claim that telemetry proves AI use, bot use, browser
automation, platform fraud, or dishonest behavior. Use language such as "flag
for manual review", "review-worthy signal", or "requires human inspection".

Write a short report describing:

- the PsyNet experiment and participant-facing flow;
- how the `psynet-participant-quality-telemetry` skill informed the
  implementation;
- the telemetry fields and where they are recorded;
- the simulated participant profiles and their intended behaviors;
- the export or PsyNet-format data-generation process;
- the manual-review flagging rules and outputs; and
- what each signal can and cannot establish about participant quality, possible
  AI assistance, or bot-like participation.

## Evidence and provenance

Collect participant-facing evidence from the local run, preferably as a browser
video such as `participant.mp4`, showing the introduction, at least one normal
text-heavy trial, and at least one attention or comprehension check.

Include the PsyNet-format data, manual-review script output, and report in the
attempt. Record implementation provenance in `agent.json`, a concise event
timeline in `TIMELINE.md`, and reusable lessons in `LEARNINGS.md`.
