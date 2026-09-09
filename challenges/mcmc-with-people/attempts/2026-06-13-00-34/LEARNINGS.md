# Learnings

## Challenge branch discovery

The requested challenge existed on a remote feature branch but had not been merged into `origin/main`, so a normal challenge lookup failed until remote branches were searched explicitly.

*Actions:*
- **PsyNetSkills:** Document how challenge attempt agents should proceed when a requested challenge slug exists only on a remote challenge branch rather than `origin/main`. Confidence: medium. Impact: medium. Status: considering.
