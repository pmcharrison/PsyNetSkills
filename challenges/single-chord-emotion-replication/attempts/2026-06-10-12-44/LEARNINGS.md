# Learnings

## Prefer minimal participant walkthroughs for long rating studies

A long recording added little value for this challenge because the participant flow is highly repetitive once the first rating trial is visible and working.

*Actions:*
- **PsyNetSkills:** Update the attempt or recording guidance to explicitly allow short representative participant recordings for long repetitive rating experiments, while relying on automated validation for completeness. Confidence: high. Status: considering.

## Local export and dashboard monitor friction in debug mode

The experiment itself ran locally, but `psynet export local` depended on dashboard configuration that was not available in this environment, and the dashboard monitor routes required authentication that was not documented in the challenge workflow.

*Actions:*
- **PsyNetSkills:** Add Cursor Cloud notes for collecting `monitor.html` and `data.zip` when dashboard auth is unavailable in local debug mode. Confidence: medium. Status: considering.
