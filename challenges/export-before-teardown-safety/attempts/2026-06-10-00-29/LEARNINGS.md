# Learnings

## Attempt author metadata needs an explicit default workflow

The challenge attempt workflow requires a registered human GitHub key in
`agent.json`, but autonomous runs may begin before the requester provides an
author key.

*Actions:*

- **PsyNetSkills:** Clarify whether autonomous challenge attempts should use a requester-provided key, a challenge-owner fallback, or a dedicated agent-attribution placeholder when no human author key is supplied. Confidence: medium. Status: considering.

## Operations plans should distinguish review commands from execution commands

Evaluation feedback noted that commands such as `find` may be too
execution-oriented when a challenge asks for a reviewed human-readable command
plan.

*Actions:*

- **PsyNetSkills:** If future operations-plan attempts repeat this issue, update the deployment-ops guidance to prefer explicit review checklists or clearly labeled optional verification commands over broad filesystem-discovery commands. Confidence: medium. Status: considering.
