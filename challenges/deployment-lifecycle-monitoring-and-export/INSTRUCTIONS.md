---
title: Deployment Lifecycle Monitoring and Export
type: operations
difficulty: 6
authors: [ww577]
---

# Deployment Lifecycle Monitoring and Export

You are given a mock PsyNet deployment dossier for a study that has already been
designed but has not yet been approved for a live launch. Your task is to write a
lifecycle-safe monitoring, export, and teardown plan aligned with PsyNet lab
deployment practice. The plan should help a future operator move from local
validation through final teardown without losing data, interrupting recruitment
incorrectly, or running destructive commands too early.

Use only the mock information in `references/mock-deployment-dossier.md`. Do not
use or request real Prolific, Cint, AWS, dashboard, Dozzle, SSH, database, API,
credential, URL, or participant information. Treat all names, links, statuses,
and examples in the dossier as fictional.

## Procedure

Produce a reviewed written plan, not an executed deployment. The plan must cover
the full lifecycle in order:

1. Design and preflight checks before deployment.
2. Local debug testing.
3. Bot testing.
4. Pilot launch checks.
5. Live deployment readiness.
6. Ongoing monitoring.
7. Regular exports and sanity checks.
8. Final export.
9. Recruitment termination or pause.
10. Application and server teardown.

For each lifecycle phase, describe the purpose of the phase, the operator checks
to perform, the evidence that would make it safe to proceed, and the conditions
that should block progress. Include dashboard and Dozzle or log monitoring
checks, and include `basic_data` or deployment-monitor checks when such outputs
are available. The export section should require regular exports during the
deployment and an `export.py`-style sanity check or equivalent analysis script
that verifies completeness, obvious data-quality problems, and expected study
counts before the operator relies on the export.

The teardown section must be conservative. Require a final successful export
before any destructive app or server action, explain recruiter stop/check
requirements before app destruction or redeployment, and distinguish PsyNet app
destruction through `psynet destroy ssh` from Dallinger EC2 server teardown. The
plan should name the commands or command families that would be reviewed by a
human operator, but it must not actually run live deployment, export, destroy,
cloud, recruiter, SSH, or credential-dependent commands.

## Deliverable

Submit a single Markdown plan that includes:

- A short summary of the mock deployment dossier.
- A lifecycle checklist in the required order.
- Monitoring checks for dashboard state, Dozzle or logs, and available
  `basic_data` or deployment-monitor outputs.
- Export cadence, export file handling, and sanity-check requirements.
- Final export and recruiter stop/check gates before destructive actions.
- Safe teardown guidance that separates app destruction from server teardown.
- A short risk register listing the most important ways the lifecycle could go
  wrong and how the plan prevents them.
