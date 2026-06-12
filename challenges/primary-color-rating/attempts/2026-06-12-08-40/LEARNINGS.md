# Learnings

## Attempt template path should be explicit

The attempt workflow says to use `assets/attempt-template/`, but the actual files are located under `.cursor/skills/attempt-challenge/assets/attempt-template/`. This was quick to resolve, but the instruction can send agents to a nonexistent repository-root path first.

*Actions:*

- **PsyNetSkills:** Clarify the `attempt-challenge` skill template path as `.cursor/skills/attempt-challenge/assets/attempt-template/` or explicitly state that `assets/attempt-template/` is relative to the skill directory. Confidence: high. Impact: low. Status: completed. Notes: The attempt workflow now makes early setup paths and paused metadata behavior explicit.

## Plan-review pauses need first-class validation and dashboard support

The experiment implementation workflow can require a pause after `PLAN.md` but before implementation evidence, authorship, or criteria review is complete. Treating that checkpoint as an invalid attempt blocks PR previews exactly when the user needs the dashboard plan link.

*Actions:*

- **PsyNetSkills:** Treat `agent.json` with `ended_at: null` as an explicit in-progress attempt state in validation, render `PLAN.md` near the top of attempt dashboard pages, and instruct agents to share the `#plan` preview link or paste the plan when previews are unavailable. Confidence: high. Impact: medium. Status: completed.
