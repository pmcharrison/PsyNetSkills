# Learnings

## Non-executable deployment plans need explicit evidence framing

This challenge intentionally forbids live deployment, export, SSH, cloud, recruiter, and teardown commands. The attempt still benefits from an evidence file that states which commands were not run and why, so reviewers do not mistake the absence of deployment logs for an accidental omission.

*Actions:*
- **PsyNetSkills:** Add a lightweight evidence checklist for operations-plan challenges that asks agents to record prohibited live actions separately from validation commands. Confidence: medium. Status: completed. Notes: Implemented in `.cursor/skills/psynet-deployment-ops/SKILL.md` with pointers from `attempt-challenge`.

## Richer mock export artifacts improve operations-plan evaluation

The human evaluator noted that future deployment-lifecycle challenges would be
stronger if the mock dossier included concrete export artifacts, file names, and
counts. That would let agents validate specific export-handling details instead
of only writing conservative planning gates around fictional exports.

*Actions:*
- **PsyNetSkills:** Add small mock export summaries or archive manifests to operations-plan challenges that require export lifecycle planning. Confidence: medium. Status: completed. Notes: Implemented in `.cursor/skills/psynet-deployment-ops/SKILL.md` with a pointer from `create-challenge`.
