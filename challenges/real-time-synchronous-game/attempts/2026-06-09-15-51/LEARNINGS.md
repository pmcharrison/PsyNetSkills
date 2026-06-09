# Learnings

## Pairing timeout needs manual-test headroom

The first visual two-browser run failed before the game page because the default `SimpleGrouper` wait window was too short for manually advancing two independent browser sessions through ad and instruction pages. Extending `max_wait_time` made the same dyad flow testable without changing the grouping design.

*Actions:*
- **PsyNetSkills:** Mention an explicit pairing wait window in future real-time sync challenge guidance when participant evidence is expected from manual or semi-manual browser sessions. Confidence: high. Status: considering.

## Use absolute export paths

`psynet export local --legacy` changed context during export, so a relative evidence path resolved outside the attempt directory and failed. An absolute export path avoided the ambiguity and produced the database archive.

*Actions:*
- **PsyNetSkills:** Update evidence-collection guidance to recommend absolute paths for `psynet export local --path` inside challenge attempts. Confidence: medium. Status: considering.
