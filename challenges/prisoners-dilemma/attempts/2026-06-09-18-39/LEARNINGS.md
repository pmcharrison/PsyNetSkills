# Learnings

## Human-paced synchronized trials need explicit wait budgets

The default pairing and sync-trial waits were sufficient for automated bots but
too short for manual two-tab participant testing. Extending the initial grouper,
round barriers, and internal sync trial-maker wait fixed premature early exits.

*Actions:*
- **PsyNetSkills:** Add a note to synchronous-game challenge guidance about setting human-paced `max_wait_time` and `sync_group_max_wait_time` before collecting participant videos. Confidence: high. Status: considering.
- **PsyNet:** Consider exposing `sync_group_max_wait_time` directly on `StaticTrialMaker` so experiment code does not need to duplicate constructor plumbing. Confidence: medium. Status: considering.
