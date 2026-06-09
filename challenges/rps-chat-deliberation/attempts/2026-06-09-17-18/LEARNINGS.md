# Learnings

## Grouped browser evidence needs explicit wait headroom

The base RPS grouping defaults are adequate for bot tests, but manual and headed-browser evidence collection can lose participants if two windows cannot be advanced at exactly the same pace. Setting explicit group and barrier wait windows made the participant-flow recording reliable without changing the pairing requirement.

*Actions:*
- **PsyNetSkills:** Add a short note to experiment-implementation guidance recommending explicit `max_wait_time` settings for grouped participant recordings. Confidence: medium. Status: considering.

## Keep demo attempts close to PsyNet idioms

Evaluator feedback emphasized that even functionally correct demo extensions should avoid custom JavaScript and extra bookkeeping when a simpler PsyNet-native pattern is acceptable. In this attempt, the countdown script and explicit deliberation start/release metadata made the solution feel less like the base demo style.

*Actions:*
- **PsyNetSkills:** Update experiment-implementation guidance to prefer "pure PsyNet" demo extensions and to treat custom JavaScript as a last resort for challenge attempts based on demos. Confidence: high. Status: considering.
- **PsyNet:** Consider adding a native timed-chat or timed-page helper for cases where automatic page advancement is needed without custom experiment JavaScript. Confidence: medium. Status: considering.
