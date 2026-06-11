# Learnings

## Non-executable deployment plans need explicit evidence framing

This challenge intentionally forbids live deployment, export, SSH, cloud, recruiter, and teardown commands. The attempt still benefits from an evidence file that states which commands were not run and why, so reviewers do not mistake the absence of deployment logs for an accidental omission.

*Actions:*
- **PsyNetSkills:** Consider adding a lightweight evidence checklist for operations-plan challenges that asks agents to record prohibited live actions separately from validation commands. Confidence: medium. Status: considering.
