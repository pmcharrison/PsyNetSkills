# Learnings

## Timed push buttons fit sequence reproduction

PsyNet's `TimedPushButtonControl` already records ordered button-click events,
which keeps a memory-sequence task simple: trial code can format the event log
into a participant response sequence without custom JavaScript.

*Actions:*
- **PsyNetSkills:** Add this pattern to experiment implementation guidance for future sequence-reproduction challenges. Confidence: high. Status: considering.
- **PsyNet:** Consider documenting `TimedPushButtonControl` as a general ordered-response control, not only a timed-response control. Confidence: medium. Status: considering.

## Dallinger import context hides sibling helpers

`psynet test local` imports the experiment through `dallinger_experiment`, so
plain sibling imports can fail even when `python experiment.py` works locally.

*Actions:*
- **PsyNetSkills:** Update generated experiment guidance to either package helper modules or prepend the experiment directory to `sys.path` before local helper imports. Confidence: high. Status: considering.
- **PsyNet:** Consider documenting the `dallinger_experiment` import context in local testing guidance. Confidence: medium. Status: considering.

## Keep PsyNet config in one place

PsyNet rejects config variables declared both in `config.txt` and on the
experiment class. Small generated experiments should choose one source of truth.

*Actions:*
- **PsyNetSkills:** Add a reminder to generated experiment templates to avoid duplicating config keys across files. Confidence: high. Status: considering.

## Constraints file is part of local PsyNet validation

`psynet test local` checks Python dependencies through `constraints.txt`, so a
minimal experiment folder with only `requirements.txt` is not enough.

*Actions:*
- **PsyNetSkills:** Include `dallinger constraints generate` in the experiment-attempt setup checklist. Confidence: high. Status: considering.
- **PsyNet:** Consider having `psynet test local` explain how to generate missing constraints. Confidence: medium. Status: considering.

## Ignore generated PsyNet archive state

PsyNet local launch writes archive/deployment files and explicitly requires
`source_code.zip` to be ignored before continuing.

*Actions:*
- **PsyNetSkills:** Add `.deploy/` and `source_code.zip` to generated PsyNet experiment `.gitignore` files. Confidence: high. Status: considering.

## Static nodes may not appear in manifest order

The participant recording showed static nodes can appear in a different order
than the manifest. Participant-facing labels should avoid implying a trial
ordinal unless the trial maker explicitly enforces that order.

*Actions:*
- **PsyNetSkills:** Advise attempt authors to phrase static-trial labels as stimulus IDs or explicitly configure trial ordering. Confidence: high. Status: considering.
- **PsyNet:** Consider making static trial ordering behavior more prominent in docs. Confidence: medium. Status: considering.

## Participant recorder needs sync calibration

The shared-desktop ffmpeg recorder can put browser audio ahead of the screen
capture. A synthetic flash/beep probe showed the isolated Xvfb capture still
needed a 2080 ms audio delay to align repeated visual and audio markers within
one video frame.

*Actions:*
- **PsyNetSkills:** Update participant-recording guidance to use an isolated Xvfb display, a dedicated PulseAudio null sink, and a flash/beep sync probe before publishing audio-sensitive evidence. Confidence: high. Status: completed. Notes: Updated `record-participant-video` with calibrated recording and post-processing guidance.

## Audio memory tasks need baseline participant affordances

The human evaluation highlighted several design expectations that were not
explicit in the challenge prompt: disable advancement until audio completes,
hide internal stimulus IDs, show audio progress/status, support keyboard input,
and include volume calibration plus a practice trial.

*Actions:*
- **PsyNetSkills:** Add audio-experiment design guidance to challenge-attempt or experiment-implementation instructions, covering calibration, practice, response modality, hidden stimulus identifiers, and audio playback state. Confidence: high. Status: considering.
- **PsyNet:** Consider a documented pattern or helper for audio memory trials with playback state, keyboard shortcuts, and response gating. Confidence: medium. Status: considering.

## Challenge attempts may need an explicit design checkpoint

The evaluator suggested a planning phase before implementation for open-ended
experiment challenges, where the agent asks about design choices such as
training, feedback, response modality, and calibration.

*Actions:*
- **PsyNetSkills:** Discuss whether `attempt-challenge` should include a short design-checkpoint option for underspecified experiment challenges before code is written. Confidence: medium. Status: considering.

## Performance evidence should be a required artifact

This attempt initially omitted `performance.json` because the guidance allowed
technical validation from "equivalent local checks." That made a missing standard
artifact too easy to rationalize.

*Actions:*
- **PsyNetSkills:** Require `evidence/performance.json` from `psynet performance-test`, or a saved `performance-test.log` plus an explicit blocker in `EVALUATION.md`; do not allow replacement by equivalent local checks. Confidence: high. Status: completed. Notes: Updated `attempt-challenge` evidence expectations and final artifact checklist.

## Bot overrides must preserve performance-test compatibility

The first performance-test run produced `performance.json` but all bots failed
before reaching the database because the experiment overrode `run_bot(cls, bot,
...)` without allowing PsyNet's no-argument `exp.run_bot(time_factor=...)`
performance-test path.

*Actions:*
- **PsyNetSkills:** Add guidance that custom `run_bot` methods should keep `bot=None` support and delegate to `super().run_bot(...)` for framework-created bots. Confidence: high. Status: completed. Notes: Updated experiment validation guidance after the performance-test failure exposed the incompatible signature.
- **PsyNet:** Consider warning when an experiment overrides `run_bot` with an incompatible signature before running `performance-test`. Confidence: medium. Status: considering.
