# Learnings

## Author metadata blocks full autonomy

The attempt workflow requires human author confirmation, but challenge attempts
are often launched as single autonomous commands. The run proceeded with the only
registered author key so the metadata remained schema-compatible.

*Actions:*
- **PsyNetSkills:** Clarify the launch prompt or attempt skill with a default author policy for autonomous challenge attempts. Confidence: medium. Status: considering.

## Participant recording needs a deterministic runner

Manual handoff made the first recording attempt too long and hard to review. A
small Selenium runner produced a concise, repeatable participant video and action
log without adding a new npm dependency.

*Actions:*
- **PsyNetSkills:** Consider documenting a Selenium fallback for participant videos when Playwright is not already installed. Confidence: medium. Status: considering.

## Local export credential handling is easy to miss

`psynet export local` needed `dashboard_user` and `dashboard_password` in the
environment even when `--username` and `--password` were passed.

*Actions:*
- **PsyNet:** Review whether `psynet export local --username/--password` should populate the dashboard export request credentials. Confidence: medium. Status: considering.
