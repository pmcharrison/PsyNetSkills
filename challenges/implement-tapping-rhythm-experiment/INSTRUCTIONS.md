---
title: Implement tapping rhythm experiment
type: experiment implementation
difficulty: 6
authors: [williambotticelli-wells]
---

Implement a small, public-safe PsyNet experiment in which participants hear
generated tones or metronome audio and tap along to the beat. The experiment
should be suitable for a local Cloud Agent attempt: compact enough to implement,
simulate, export, analyze, and document without relying on private data,
copyrighted stimuli, production deployment details, real recruitment, or
credentials.

Use only generated audio assets created by the attempt code, such as sine tones,
click tracks, or metronome patterns. Do not use private file paths, proprietary
recordings, copyrighted music, AWS/Prolific/Cint credentials, real deployment
logs, or production service configuration.

## Relevant skills

Use the repository skills that match this task:

- `psynet-tapping-experiments`
- `psynet-simulated-participants`
- `psynet-experiment-implementation`
- `psychophysics`
- `record-participant-video`

The implementation should follow those skills for timing-sensitive audio,
tapping data, simulated profiles, participant-facing evidence, analysis, and
limitations reporting.

## Participant experience

Create a short participant flow with the following stages:

1. A concise introduction explaining that the participant will hear simple
   generated tones or metronome clicks and tap in time with them.
2. An audio playback or volume check using representative generated audio.
3. A calibration or practice section with at least one simple isochronous
   metronome pattern. The participant should receive clear start/stop cues and
   should not enter the main task until the calibration/practice path records a
   usable status.
4. A small main task with several tapping trials. Each trial should play a
   generated rhythmic stimulus and collect tap onsets during the intended tapping
   window.
5. A clean completion path, plus a clear failure or dropout path for simulated
   participants that do not provide usable tapping data.

Keyboard or pointer taps are acceptable. Microphone-based tap detection is not
required, but the saved data should still expose tap onset fields that can be
checked and analyzed.

## Stimuli and timing

Keep the stimulus set small. Include stable stimulus identifiers and enough
metadata to distinguish the generated patterns, for example tempo, number of
beats, beat interval, condition label, and generated audio filename or asset key.

Use explicit timing constants for pre-roll, playback, tapping windows, and
post-roll. The participant-facing timing cues, response window, saved tap onset
times, and analysis assumptions should be consistent with those constants.

## Simulated participants

Implement local simulated participants or scripted profiles that exercise both
successful and failing paths. Include at least these five profiles:

- `good`: passes calibration and produces plausible taps near the target tempo;
- `too-few-taps`: produces too few taps to pass the minimum-tap threshold;
- `off-tempo`: taps consistently at the wrong tempo;
- `noisy`: produces high-variability tap timing;
- `dropout`: exits early, omits required responses, or otherwise produces an
  incomplete record.

Record the simulated profile id in export-visible participant or trial metadata.
The profiles should interact with the same response formatting, trial saving,
failure flags, and export paths used by the main experiment rather than only
manufacturing an analysis fixture.

## Validation and export checks

Run the experiment locally with the simulated profiles. Include participant-facing
evidence, preferably a short `evidence/participant.mp4`, that shows audio
playback, calibration or practice, and at least one main tapping trial.

Export local or simulated PsyNet-format data and add checks that verify:

- participant rows exist and include simulated profile metadata;
- trial rows exist for calibration/practice and main tapping trials;
- stimulus ids in trial rows match the generated stimulus manifest or metadata;
- tap onset fields are present and parseable;
- calibration status is saved for each participant or relevant trial;
- failure flags and failure reasons are present for failed profiles;
- the dropout profile is distinguishable from ordinary failed tapping trials.

These checks may be a focused script, notebook section, or test command, but they
must be runnable from the committed attempt materials.

## Analysis

Write a short analysis notebook or script that reads the exported or clearly
documented simulated PsyNet-format data and summarizes:

- taps per trial;
- inter-tap intervals;
- valid versus failed trials;
- calibration outcomes;
- failure flags and reasons;
- coverage by simulated profile.

The analysis should produce small tables or concise plots that a reviewer can
inspect quickly. It should fail clearly or report missing fields if the expected
export columns are absent.

## Report

Write `REPORT.md` with concise methods, validation, analysis, and limitations
sections. The report must explicitly state that simulated tapping validates the
experiment workflow and analysis code, not human rhythm perception.

## Deliverables

Include the following in the attempt:

- runnable PsyNet experiment code using generated tones or metronome audio only;
- a small generated-stimulus manifest or equivalent metadata;
- simulated participant profiles for `good`, `too-few-taps`, `off-tempo`,
  `noisy`, and `dropout`;
- local run and export evidence;
- export checks covering participant rows, trial rows, stimulus ids, tap onset
  fields, calibration status, and failure flags;
- a short analysis notebook or script with outputs;
- participant-facing evidence showing the tapping flow;
- `REPORT.md`, `agent.json`, `TIMELINE.md`, and `LEARNINGS.md`.
