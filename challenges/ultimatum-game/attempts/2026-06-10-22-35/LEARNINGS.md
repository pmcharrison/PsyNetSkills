# Learnings

## Takeover attempts need explicit architecture notes

The prior attempt solved most behavior but used a monolithic custom page/state machine. The user-requested takeover required reading both the evaluation and the external reference architecture before writing code, because the important change was structural rather than just visual.

*Actions:*
- **PsyNetSkills:** Consider adding a takeover checklist that asks agents to record which prior-attempt weaknesses are being addressed and which architecture source should be mimicked. Confidence: medium. Status: considering.

## Dashboard monitor evidence route changed

The old `/dashboard/monitor` route returned 404 on this PsyNet checkout. The equivalent monitor-style evidence was the `Basic data` dashboard tab at `/dashboard/data`, which calls `get_basic_data(context="monitor")`.

*Actions:*
- **PsyNetSkills:** Consider updating experiment evidence guidance to say `monitor.html` may be captured from `/dashboard/data` on current PsyNet versions. Confidence: high. Status: considering.
