# Learnings

## Pairing timeout needs manual-test headroom

The first visual two-browser run failed before the game page because the default `SimpleGrouper` wait window was too short for manually advancing two independent browser sessions through ad and instruction pages. Extending `max_wait_time` made the same dyad flow testable without changing the grouping design.

*Actions:*
- **PsyNetSkills:** Mention an explicit pairing wait window in future real-time sync challenge guidance when participant evidence is expected from manual or semi-manual browser sessions. Confidence: high. Impact: medium. Status: considering.
## Use absolute export paths

`psynet export local --legacy` changed context during export, so a relative evidence path resolved outside the attempt directory and failed. An absolute export path avoided the ambiguity and produced the database archive.

*Actions:*
- **PsyNetSkills:** Update evidence-collection guidance to recommend absolute paths for `psynet export local --path` inside challenge attempts. Confidence: medium. Impact: low. Status: considering.
## Review recordings for interaction semantics

The first successful visual recording showed realtime heatmap updates, but video review caught that participant round counters advanced independently after each participant's own click. A second implementation pass made the grid wait for both dyad members before advancing rounds, and a second recording verified the corrected behavior.

*Actions:*
- **PsyNetSkills:** Keep video review as an explicit evidence-validation step for synchronous/interacting-participant challenges, not just a final artifact check. Confidence: high. Impact: high. Status: considering.
