# Learnings

## Attempt template path should be explicit

The attempt workflow says to use `assets/attempt-template/`, but the actual files are located under `.cursor/skills/attempt-challenge/assets/attempt-template/`. This was quick to resolve, but the instruction can send agents to a nonexistent repository-root path first.

*Actions:*

- **PsyNetSkills:** Clarify the `attempt-challenge` skill template path as `.cursor/skills/attempt-challenge/assets/attempt-template/` or explicitly state that `assets/attempt-template/` is relative to the skill directory. Confidence: high. Impact: low. Status: considering.
