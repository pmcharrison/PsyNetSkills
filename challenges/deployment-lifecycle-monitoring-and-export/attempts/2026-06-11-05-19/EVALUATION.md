---
score:
---

# Evaluation

## Summary

Summarize the human evaluator's overall judgment.

## Strengths

- 

## Weaknesses

- 

## Criteria

Ask the evaluator about each criterion and record the result here.

- [ ] The plan follows the lifecycle: design/test, local debug, bot test, pilot, deploy, monitor, export, final export, terminate, teardown.
- [ ] The plan includes dashboard and Dozzle/log monitoring checks.
- [ ] The plan mentions `basic_data` or deployment-monitor checks when available.
- [ ] The plan requires regular exports and an `export.py`-style sanity check or equivalent analysis script.
- [ ] The plan requires a final export before any destructive app/server action.
- [ ] The plan distinguishes `psynet destroy ssh` from Dallinger EC2 teardown.
- [ ] The plan mentions recruiter stop/check requirements before app destruction or redeployment.
- [ ] The plan does not use real Prolific, Cint, AWS, credentials, URLs, or participant data.
- [ ] The plan is a reviewed plan only and does not run live deployment/export/destroy commands.

## Notes

- Score and feedback should come from a human evaluator, captured
  conversationally when working with Cursor Cloud Agents.
