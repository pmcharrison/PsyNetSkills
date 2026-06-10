# Learnings

## Attempt author metadata needs an explicit default workflow

The challenge attempt workflow requires a registered human GitHub key in
`agent.json`, but autonomous runs may begin before the requester provides an
author key.

*Actions:*

- **PsyNetSkills:** Clarify whether autonomous challenge attempts should use a requester-provided key, a challenge-owner fallback, or a dedicated agent-attribution placeholder when no human author key is supplied. Confidence: medium. Status: considering.
