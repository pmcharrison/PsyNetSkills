# Learnings

## Completed attempts need an explicit human author key

The author-identification workflow correctly prevents inferring authorship from the runtime user or challenge author, but completed attempt validation requires a non-empty `agent.json` author list.

*Actions:*

- **PsyNetSkills:** Clarify in `attempt-challenge/SKILL.md` how Cloud agents should handle full implementation requests when no human GitHub username is available at attempt start. Confidence: high. Impact: medium. Status: considering. Notes: This avoids either blocking long-running evidence work or leaving otherwise complete attempts marked in progress.
