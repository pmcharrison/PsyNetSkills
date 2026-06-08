# Learnings

## Avoid running Dallinger from a directory named code

`psynet test local` imports the current experiment directory as a Python package.
When the directory is literally named `code`, Dallinger can collide with
Python's standard-library `code` module before it sees the local package. A
non-conflicting nested experiment directory avoids this.

*Actions:*
- **PsyNetSkills:** Document in the attempt-challenge skill that runnable PsyNet experiments should live in a non-conflicting subdirectory under `code/` when the dashboard schema requires a top-level `code/` folder. Confidence: high. Status: considering.
- **PsyNet:** Consider making Dallinger's experiment package initialization robust to basenames that collide with already-imported stdlib modules. Confidence: medium. Status: considering.

## Capture browser audio with a PulseAudio null sink

The VM initially exposed no PulseAudio or PipeWire source, and ALSA only listed
`null`. Installing PulseAudio and recording a `module-null-sink` monitor made
browser audio capture work once Chrome was launched with `PULSE_SERVER` pointed
at that server.

*Actions:*
- **PsyNetSkills:** Add a Linux fallback to the recording skill that installs/starts PulseAudio, creates `psynet_rec`, launches Chrome with `PULSE_SERVER`, and records `psynet_rec.monitor`. Confidence: high. Status: considering.
- **PsyNet:** No framework change needed; this is a cloud recording environment setup issue. Confidence: medium. Status: dismissed.

## Combine minimal visual review with scripted full-flow evidence

A shortened `PSYNET_PROFILE=minimal` run gave the visual reviewer enough surface
to inspect copy, labels, button state, reset behavior, and completion. A
JavaScript Playwright-driven full run then produced a concise participant video
with audio, replacing a much slower agent-driven recording. The best
illustrative recording used the script's `--human-time` option so reviewers
could see the individual clicks and complete staged responses.

*Actions:*
- **PsyNetSkills:** Make the default challenge evidence workflow hybrid: use minimal profile for visual review screenshots, then use a JavaScript Playwright runner in human-time mode for the canonical recorded flow. Confidence: high. Status: considering.
- **PsyNet:** Consider a framework-level `PSYNET_PROFILE=minimal` convention for skipping or shortening standard components during local review while preserving custom experiment behavior. Confidence: medium. Status: considering.
