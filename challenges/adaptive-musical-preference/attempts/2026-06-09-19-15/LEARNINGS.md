# Learnings

## Recompute on-demand asset URLs after insertion

PsyNet's on-demand asset URL can be computed before the asset has a database ID
when it is added during trial definition finalization. Recomputing the URL after
`add_assets` prevents browser requests such as `/on-demand-asset?id=None`.

*Actions:*
- **PsyNetSkills:** Add an example or validation note for on-demand assets created inside `finalize_definition`. Confidence: medium. Status: considering.
- **PsyNet:** Consider recomputing on-demand asset URLs automatically after insert. Confidence: medium. Status: considering.

## Cursor Cloud audio evidence needs a browser routing check

The participant video captured the full visual flow, but the PulseAudio monitor
recorded an effectively silent track even after using a null sink and an
isolated Chrome profile. A short preflight that verifies browser audio reaches
the monitor would catch this before a full participant run.

*Actions:*
- **PsyNetSkills:** Extend `record-participant-video` with a browser-audio preflight check in Cursor Cloud. Confidence: high. Status: considering.
