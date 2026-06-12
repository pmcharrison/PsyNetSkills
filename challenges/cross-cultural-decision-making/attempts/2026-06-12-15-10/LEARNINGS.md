# Learnings

## Limit slug searches to current challenge files

While resolving the typoed challenge name, a broad repository search returned public instruction snapshots inside prior attempt folders. Future challenge attempts should search only top-level `challenges/*/INSTRUCTIONS.md` files during the pre-implementation phase.

*Actions:*

- **PsyNetSkills:** Clarify the `attempt-challenge` skill with an explicit top-level challenge-search pattern that excludes `attempts/` until implementation and evidence collection are complete. Confidence: high. Impact: medium. Status: considering.
