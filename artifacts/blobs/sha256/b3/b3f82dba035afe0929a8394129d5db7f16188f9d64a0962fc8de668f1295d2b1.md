---
title: End-to-end simulated PsyNet discovery
type: experiment implementation
difficulty: 8
authors: [williambotticelli-wells]
---

Implement a small PsyNet experiment from the prose research prompt below, run it
locally with bot or simulated participants, export the local PsyNet data, analyze
the exported data, and write a short methods/results report.

## Research prompt

Design a brief discovery-oriented experiment asking whether short surprising
facts elicit stronger curiosity than ordinary facts. Participants should see a
small set of text stimuli, with each stimulus labelled internally as either
`surprising` or `ordinary`. On each trial, participants should rate how curious
they are to learn more about the fact on a simple numeric scale. The participant
experience should include a concise introduction, trial pages with clear
instructions, and a closing page.

The implementation may use a compact hand-authored stimulus set. The study is
intended as a local end-to-end PsyNet demonstration, not as a valid psychology
claim about human curiosity.

## Required work

Create a runnable PsyNet experiment that implements the research prompt. The
experiment should save enough trial-level data to connect each response to the
stimulus text, stimulus condition, participant, and response value.

Run the experiment locally with PsyNet bot or simulated participants. Do not use
real Prolific, Cint, AWS, paid recruitment, production credentials, or any other
external participant-recruitment or production-service workflow. Use only local
PsyNet data and mock or simulated participants.

Collect participant-facing evidence from the local run, preferably as a browser
video such as `participant.mp4`. The evidence should show the participant flow
through the implemented experiment rather than only terminal output.

Export the local PsyNet data after the run. Include evidence showing where the
exported data was written and enough exported content or metadata for a reviewer
to confirm that the experiment produced local data.

Write an analysis script that runs on the exported data, or on a clearly
documented PsyNet-format local simulation derived from the export if the export
format needs light normalization. The analysis should report basic descriptive
results such as participant count, trial count, and curiosity ratings summarized
by stimulus condition.

Write a short methods/results report. The report should describe the implemented
task, the local bot or simulated participant procedure, the exported data used by
the analysis, and the resulting descriptive statistics. It should clearly
distinguish actual PsyNet output from simulated participant behavior and should
avoid claiming that bots reproduce human psychological behavior.

Record implementation provenance in `agent.json`, a concise event timeline in
`TIMELINE.md`, and reusable lessons in `LEARNINGS.md`.
