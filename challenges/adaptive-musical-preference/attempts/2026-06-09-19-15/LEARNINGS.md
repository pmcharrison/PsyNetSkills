# Learnings

## Recompute on-demand asset URLs after insertion

PsyNet's on-demand asset URL can be computed before the asset has a database ID
when it is added during trial definition finalization. Recomputing the URL after
`add_assets` prevents browser requests such as `/on-demand-asset?id=None`.

*Actions:*
- **PsyNetSkills:** Add an example or validation note for on-demand assets created inside `finalize_definition`. Confidence: medium. Status: considering.
- **PsyNet:** Consider recomputing on-demand asset URLs automatically after insert. Confidence: medium. Status: considering.

## Cursor Cloud audio evidence needs isolated browser routing

Chrome reused an existing process at first, so the PulseAudio monitor recorded an
effectively silent track. Launching a fresh Chrome profile with `PULSE_SERVER`
pointing at the null sink produced non-silent participant evidence. A short
preflight that verifies browser audio reaches the monitor would catch this before
a full participant run.

*Actions:*
- **PsyNetSkills:** Extend `record-participant-video` with a browser-audio preflight check in Cursor Cloud. Confidence: high. Status: considering.

## Performance evidence should foreground completion rate

The performance test reported zero bot/request errors, but the human evaluation
still flagged that about half of the attempts did not complete within the fixed
test window. Future summaries should report both error rate and completion rate
prominently.

*Actions:*
- **PsyNetSkills:** Clarify challenge evidence guidance to interpret performance-test timeout/incomplete counts separately from request or bot errors. Confidence: medium. Status: considering.
