---
title: Monitor PsyNet Experiment Run
type: experiment operations
difficulty: 6
authors: [williambotticelli-wells]
---

# Monitor PsyNet Experiment Run

You are given a fictional dossier for a local/mock PsyNet experiment run. Your
task is to inspect the available evidence, write a conservative monitoring log,
and make one operational decision about whether the run should continue, be
watched, pause, stop for fixes, or be exported and handed off.

Use only the mock information in `references/mock-experiment-run-dossier.md`.
Do not use or request real AWS, recruiter, dashboard, SSH, database, API,
credential, URL, paid-participant, app-destruction, or EC2-teardown access.
Treat all app names, server names, links, logs, participant identifiers, export
paths, and data summaries in the dossier as fictional.

## Scenario

The dossier describes a short local pilot of a PsyNet pitch-memory experiment.
It includes mock app and server names, a local recruiter setup, expected
participant and trial counts, participant-flow notes, deployment-style logs,
and exported-data summaries. The run contains at least one ambiguous issue: a
completed participant has review-worthy telemetry, and one started participant
has not completed. Your job is to decide conservatively from the evidence,
without inventing unavailable access or treating ambiguous quality signals as
proof of fraud or scientific failure.

## Procedure

Create `MONITORING_LOG.md` in your attempt folder. The log should be written as
an operations note that a human lab member could review before deciding what to
do next.

Your monitoring log must include:

1. **Scope and access**
   - Experiment folder and branch from the dossier.
   - App name and server name.
   - Dashboard or preview URL, if provided.
   - Recruiter state and whether the run is local/mock, pilot, production, or
     post-run export.
   - Expected participant count or stopping rule.
   - Expected trial, module, or task counts per participant.
   - Any unavailable access or explicit blockers.
2. **Participant-flow health checks**
   - Consent or ad page.
   - Instructions.
   - Media and asset loading, including audio or other stimulus assets.
   - Representative trial completion.
   - Prescreener or failure path, if present.
   - Completion redirect or end page.
3. **Operational health checks**
   - Whether app, server, and export names match the dossier.
   - Whether logs show an obvious error loop, missing assets, stalled queues, or
     resource-risk pattern.
   - Whether participant counts move in a way that is plausible for the stated
     stopping rule.
4. **Export-readiness checks**
   - Participant rows.
   - Trial rows.
   - Module states or an equivalent PsyNet state summary.
   - Key metadata fields needed for analysis and audit.
   - Condition assignment or grouping.
   - Quality flags or participant-quality telemetry.
   - Export path and whether export is ready, partial, blocked, or only suitable
     for interim review.
5. **Decision**
   - Choose exactly one label: `continue`, `continue-with-watch`, `pause`,
     `stop-and-fix`, or `export-and-handoff`.
   - Justify the label using evidence from the dossier.
   - State what would make you change the decision.
6. **Remaining human action**
   - List any decisions, checks, or approvals that still require a human.
   - Make clear that destructive commands, real deployment changes, real
     recruitment changes, and paid-resource teardown are outside this challenge.

Be conservative. It is acceptable to recommend watching, pausing, or fixing when
evidence is incomplete or participant welfare, payment, data integrity, or
scientific validity is uncertain. It is not acceptable to run real deployment
commands, invent credentials, claim that telemetry proves a participant is a bot
or AI user, or recommend app/server destruction as part of this task.

## Deliverable

Submit `MONITORING_LOG.md` with:

- A concise dossier summary.
- A participant-flow health section.
- An operational health section.
- An export-readiness section.
- One decision label and evidence-based justification.
- Remaining human action.
- Clear notes about any blockers, uncertainties, and mock-only assumptions.
