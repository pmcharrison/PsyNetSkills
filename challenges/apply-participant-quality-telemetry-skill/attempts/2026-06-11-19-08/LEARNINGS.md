# Learnings

## Include the full PsyNet experiment support template

Starting from only `experiment.py`, `config.txt`, and `requirements.txt` made
`psynet test local` fail before exercising the experiment because `test.py` and
`constraints.txt` were missing.

*Actions:*
- **PsyNetSkills:** Update the `attempt-challenge` or `psynet-experiment-implementation` guidance to list `test.py` and generated `constraints.txt` alongside `.gitignore` as required files for self-contained PsyNet challenge attempts. Confidence: high. Impact: high. Status: considering.

## Verify browser-path JavaScript, not only bot-path telemetry

The bot test passed after server-side fixes, but manual recording found that the
browser script used `psynet.page.js_vars`, while PsyNet exposes page variables
through `psynet.var` and globals.

*Actions:*
- **PsyNetSkills:** Add a reminder to `psynet-participant-quality-telemetry` that custom telemetry JavaScript should be manually exercised in a browser because PsyNet bots can bypass client-side event collection. Confidence: high. Impact: high. Status: considering.
- **PsyNet:** Consider documenting the recommended JavaScript access pattern for page `js_vars` near the `ModularPage` or `Page` API docs. Confidence: medium. Impact: medium. Status: considering.

## Review participant videos before accepting them

The first successful-looking participant recording ended at the attention check
because the fixed-duration capture stopped before the completion page.

*Actions:*
- **PsyNetSkills:** Keep the `videoReview` verification step for participant evidence and prefer stopping `ffmpeg` immediately after completion rather than relying on a tight fixed-duration cap. Confidence: high. Impact: high. Status: considering.

## Stress-test telemetry rules with ambiguous profiles

The evaluation noted that the attempt validated the telemetry skill well, but
the simulated profiles were cleanly separated. Richer experimental paradigms and
more ambiguous participant profiles would better test whether manual-review
rules remain conservative under realistic uncertainty.

*Actions:*
- **PsyNetSkills:** Add a future participant-quality telemetry challenge or example that uses a richer real experimental paradigm with ambiguous participant profiles, so review rules are tested against overlapping quality signals rather than clearly separated attentive and suspicious fixtures. Confidence: medium. Impact: medium. Status: considering.
