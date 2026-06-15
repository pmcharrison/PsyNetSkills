# Learnings

## Completed attempts need an explicit human author key

The author-identification workflow correctly prevents inferring authorship from the runtime user or challenge author, but completed attempt validation requires a non-empty `agent.json` author list.

*Actions:*

- **PsyNetSkills:** Clarify in `attempt-challenge/SKILL.md` how Cloud agents should handle full implementation requests when no human GitHub username is available at attempt start. Confidence: high. Impact: medium. Status: considering. Notes: This avoids either blocking long-running evidence work or leaving otherwise complete attempts marked in progress.

## Specialized challenge attempts should document required skill use

This attempt followed many tapping-experiment best practices, but the evidence only says the agent read "required skills" and does not explicitly record that `psynet-tapping-experiments` was opened or used. When a challenge names a specialized skill, evaluation is easier if the timeline or report records the exact skill files consulted.

*Actions:*

- **PsyNetSkills:** Update attempt evidence guidance so agents record the exact repository skill names or paths consulted for specialized challenges, especially when criteria ask whether a specific skill was used. Confidence: high. Impact: medium. Status: considering. Notes: This creates auditable process evidence without requiring evaluators to infer skill use from implementation style.
