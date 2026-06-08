# Learnings

## Avoid running Dallinger from a directory named code

`psynet test local` imports the current experiment directory as a Python package.
When the directory is literally named `code`, Dallinger can collide with
Python's standard-library `code` module before it sees the local package. A
non-conflicting nested experiment directory avoids this.

*Actions:*
- **PsyNetSkills:** Document in the attempt-challenge skill that runnable PsyNet experiments should live in a non-conflicting subdirectory under `code/` when the dashboard schema requires a top-level `code/` folder. Confidence: high. Status: completed. Notes: Added to the attempt-challenge workflow.
- **PsyNet:** Consider making Dallinger's experiment package initialization robust to basenames that collide with already-imported stdlib modules. Confidence: medium. Status: considering.

## Capture browser audio with a PulseAudio null sink

The VM initially exposed no PulseAudio or PipeWire source, and ALSA only listed
`null`. Installing PulseAudio and recording a `module-null-sink` monitor made
browser audio capture work once Chrome was launched with `PULSE_SERVER` pointed
at that server.

*Actions:*
- **PsyNetSkills:** Add a Linux fallback to the recording skill that installs/starts PulseAudio, creates `psynet_rec`, launches Chrome with `PULSE_SERVER`, and records `psynet_rec.monitor`. Confidence: high. Status: completed. Notes: Added to the record-participant-video skill, including audio verification commands.
- **PsyNet:** No framework change needed; this is a cloud recording environment setup issue. Confidence: medium. Status: dismissed.

## Combine minimal visual review with scripted full-flow evidence

A shortened `PSYNET_PROFILE=minimal` run gave the visual reviewer enough surface
to inspect copy, labels, button state, reset behavior, and completion. A
JavaScript Playwright-driven full run then produced a concise participant video
with audio, replacing a much slower agent-driven recording. The best
illustrative recording used the script's `--human-time` option so reviewers
could see the individual clicks and complete staged responses.

*Actions:*
- **PsyNetSkills:** Make the default challenge evidence workflow hybrid: use minimal profile for visual review screenshots, then use a JavaScript Playwright runner in human-time mode for the canonical recorded flow. Confidence: high. Status: completed. Notes: Added to the attempt-challenge evidence workflow.
- **PsyNet:** Consider a framework-level `PSYNET_PROFILE=minimal` convention for skipping or shortening standard components during local review while preserving custom experiment behavior. Confidence: medium. Status: considering.

## Add task training before scored memory trials

The evaluator noted that experiments like this should normally begin with a
training phase explaining the task and giving participants a couple of practice
attempts before the main trials.

*Actions:*
- **PsyNetSkills:** Update future audio-memory-style challenge guidance to mention practice/training phases when the task is nontrivial. Confidence: high. Status: completed. Notes: Added to create-challenge and psynet-experiment-implementation guidance.
- **PsyNet:** Consider documenting a reusable pattern for practice trial makers that precede scored static trials. Confidence: medium. Status: considering.

## Avoid replay controls in memory tasks

The implementation exposed a replay button for each tone sequence. In memory
tasks, relistening can give participants a large advantage and change the
cognitive demands of the task.

*Actions:*
- **PsyNetSkills:** Add review guidance to flag replay controls in memory tasks unless the challenge explicitly asks for replay. Confidence: high. Status: completed. Notes: Added to create-challenge and psynet-experiment-implementation guidance.
- **PsyNet:** No framework change needed; this is an experiment-design convention. Confidence: high. Status: dismissed.

## Prefer generated audio files for control and replication

The evaluator would usually prefer Python-generated audio files over `JSSynth`
for this kind of experiment. Committed audio files make replication easier and
give more control over synthesis details.

*Actions:*
- **PsyNetSkills:** Encourage challenge attempts with synthesized audio stimuli to generate deterministic local audio files when feasible, and document the choice. Confidence: medium. Status: considering.
- **PsyNet:** Consider improving examples that generate and commit simple audio stimuli for static audio experiments. Confidence: medium. Status: considering.

## Store stimulus definitions outside experiment.py

Hardcoding trial sequences directly in `experiment.py` works for a small
challenge but scales poorly. A script-generated JSON stimulus file can support
random sampling, reproducibility, and manual regeneration while keeping the
runtime experiment deterministic.

*Actions:*
- **PsyNetSkills:** Add a recommendation that attempts with nontrivial stimulus sets use a generated stimulus manifest, such as committed JSON plus optional generated media. Confidence: high. Status: completed. Notes: Added to create-challenge and psynet-experiment-implementation guidance.
- **PsyNet:** Consider documenting a standard manifest-driven static trial pattern. Confidence: medium. Status: considering.
