# Learnings

## Native graphics pattern for timed visual discrimination

PsyNet's `GraphicPrompt` frames, `prevent_control_response`, and `KeyboardPushButtonControl` implemented the fixation, stimulus, blank, response gating, keyboard input, and reaction-time capture without custom front-end timing code.

*Actions:*

- **PsyNetSkills:** Update the psychophysics skill to recommend `GraphicPrompt` frame sequencing with `prevent_control_response`, `activate_control_response`, `KeyboardPushButtonControl`, and event-log reaction-time extraction for simple visual discrimination tasks. Confidence: high. Impact: medium. Status: considering.

## Existing-server performance tests need local dashboard credentials

Running `psynet performance-test local --existing` after `psynet debug local` failed because the command could not read `dashboard_password` from the attempt's config, while running `psynet performance-test local` in normal server-owning mode succeeded.

*Actions:*

- **PsyNetSkills:** Document that challenge attempts should prefer normal `psynet performance-test local` mode unless `dashboard_user` and `dashboard_password` are available in local config for `--existing`. Confidence: high. Impact: low. Status: considering.
- **PsyNet:** Consider allowing `psynet performance-test local --existing` to accept dashboard credentials as CLI flags or infer them from the running local deployment config. Confidence: medium. Impact: low. Status: considering.
