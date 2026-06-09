# Learnings

## Grouped browser evidence needs explicit wait headroom

The base RPS grouping defaults are adequate for bot tests, but manual and headed-browser evidence collection can lose participants if two windows cannot be advanced at exactly the same pace. Setting explicit group and barrier wait windows made the participant-flow recording reliable without changing the pairing requirement.

*Actions:*
- **PsyNetSkills:** Add a short note to experiment-implementation guidance recommending explicit `max_wait_time` settings for grouped participant recordings. Confidence: medium. Status: considering.
