---
name: psynet-tapping-experiments
description: Implement PsyNet tapping, rhythm, beat perception, sensorimotor synchronization, and REPP microphone-recorded tapping experiments with audio recording, calibration, export checks, and conservative interpretation.
authors: [williambotticelli-wells]
---

# PsyNet tapping experiments

Use this skill when a PsyNet experiment asks participants to tap along to audio,
rhythms, metronomes, clicks, or music clips. The skill owns timing-sensitive
tapping flow, recording calibration, tap-onset export checks, and interpretation
boundaries. It does not own ordinary audio rating tasks unless participants
produce timed tapping responses.

## Required reads

- Read `psynet-experiment-implementation/SKILL.md` for the general planning,
  implementation, simulation, export, analysis, and report workflow.
- Read `participant-filtering-and-prescreening/SKILL.md` before adding device,
  audio, microphone, recording, or tapping capability gates.
- Read `psychophysics/SKILL.md` when visual timing, reaction time, or exact
  stimulus display matters alongside tapping.
- Read `record-participant-video/SKILL.md` for audio-sensitive participant-flow
  evidence.
- Read `psynet-simulated-participants/SKILL.md` for bot or scripted tapping
  profiles.
- Read `psynet-deployment-ops/SKILL.md` if the work involves deployment,
  exports, recruiter setup, or teardown.
- For REPP microphone-recorded SMS experiments, inspect the local PsyNet
  examples in `~/PsyNet/demos/pipelines/tapping/` and the REPP prescreen API
  docs in `~/PsyNet/docs/api/prescreen.rst` before copying patterns.

## Participant flow

A robust tapping experiment should usually include:

1. Consent and an audio/recording notice.
2. Device and environment instructions: quiet room, appropriate browser,
   microphone permission, and the intended speaker/headphone policy.
3. Volume calibration with representative audio.
4. Recording or marker prescreening to verify usable audio/tap capture.
5. Tapping calibration with simple isochronous rhythms.
6. Practice trials with clear start/stop cues and pass/fail or feedback logic
   when appropriate.
7. Main rhythm or music tapping trials.
8. Demographic or music-background questionnaires when scientifically relevant.
9. Clean completion and recruiter redirect.

For public examples and challenges, use generated tones, generated metronomes,
short placeholder audio, or public/demo assets only.

## REPP and microphone-recorded SMS

Use REPP when the experiment needs microphone-recorded finger taps synchronized
to audio and analyzed with the REPP signal-processing pipeline. Do not require
REPP for keyboard, pointer, or other non-recorded tapping unless the task
explicitly needs REPP calibration, marker detection, or `REPPAnalysis`.

REPP experiments should use the package and framework pieces together:

- Include `repp-tapping` in the experiment environment and use
  `repp.config.sms_tapping` with `REPPStimulus` and `REPPAnalysis`.
- Use `REPPVolumeCalibrationMusic` for music stimuli, or
  `REPPVolumeCalibrationMarkers` for marker/metronome stimuli.
- Place `REPPMarkersTest` after the volume calibration to check whether the
  laptop speaker and microphone chain can recover REPP markers. Its default
  PsyNet implementation runs 3 trials, uses a 0.6 performance threshold, and
  expects all 6 markers in each test recording.
- Place `REPPTappingCalibration` before main tapping trials so participants can
  practice tapping on the laptop surface while watching the input meter.
- Keep the REPP hardware policy explicit: laptop speakers, no headphones or
  external speakers, quiet environment, and microphone permission.

For prescreener eligibility decisions, thresholds, recruiter alignment, and
whether a REPP failure should terminate participation or become a covariate,
follow `participant-filtering-and-prescreening/SKILL.md`.

Main REPP trials should follow the `~/PsyNet/demos/pipelines/tapping/` pattern:

- Build generated isochronous stimuli with
  `REPPStimulus.prepare_stim_from_onsets`.
- Build annotated music stimuli with `REPPStimulus.filter_and_add_markers`.
- Package each prepared stimulus as a folder asset containing `audio.wav` and
  `info.json`; the demo reads `info.json` with a double JSON decode.
- Use `AudioRecordTrial` with `AudioRecordControl(duration=stim_duration)`.
- Return REPP analysis fields such as `failed`, `reason`, `output`,
  `analysis`, and `stim_name` from `analyze_recording`.
- Provide local recorded tap-audio fixtures through `bot_response_media` for
  automated tests; the demo currently assumes `LocalStorage` for those fixtures.

REPP stimulus preparation changes the audio. In `repp-tapping==1.4.0`,
`sms_tapping` sets `FS = 44100`, `STIM_RANGE = [30, 1000]`, and
`STIM_AMPLITUDE = 0.12`; `filter_stim` applies a 2nd-order Butterworth bandpass
over that range twice with `filtfilt`, then normalizes `stim - filtered_stim`.
Marker insertion uses `MARKERS_RANGE = [200, 340]`, `MARKERS_AMPLITUDE = 0.9`,
`MARKERS_ATTACK = 2`, `MARKERS_DURATION = 15`, `MARKERS_IOI = [0, 280, 230]`,
`MARKERS_BEGINNING = 2000.0`, `STIM_BEGINNING = 4000.0`,
`MARKERS_END = 2000.0`, and `MARKERS_END_SLACK = 6000.0`.
For stimuli where low-frequency or full-spectrum content is scientifically
important, compare the prepared REPP output against the source stimulus and
document that the altered stimulus is acceptable before using it.

## Timing and audio rules

- Use explicit pre-roll and post-roll periods so participants know when not to
  tap.
- Use visible progress stages such as "wait in silence", "start tapping", "stop
  tapping", and "press next".
- Keep audio duration, recording duration, and progress display synchronized.
- Store timing constants centrally rather than scattering them across page text,
  controls, and analysis scripts.
- Ensure the recording window covers the full intended tapping response period.
- Use stable stimulus ids and metadata. Prefer manifests for multi-file audio
  sets or when condition metadata matters.
- Deterministic generated isochronous stimuli are acceptable for calibration,
  testing, and public examples when documented.
- Do not use ground-truth annotations to construct participant-facing
  crowd-derived outputs unless the task explicitly says so.
- Separate construction signals from validation signals:
  - construction: participant taps, derived tap onsets, internally inferred
    timing, and pooled-tap summaries;
  - validation: ground-truth annotations, listener ratings, and algorithmic
    baselines.

## Data and exports

Save enough data to reconstruct trial-level timing and stimulus assignment.
Recommended export-visible fields include:

- participant id;
- trial id;
- stimulus id or stimulus name;
- audio asset key or public-safe filename;
- condition;
- recording asset reference when available;
- raw or derived tap onset times;
- aligned tap onset times when available;
- analysis status and failure flag;
- failure reason;
- number of detected taps;
- stimulus and recording duration;
- calibration status;
- practice or isochronous tapping score;
- consented participant covariates needed for interpretation, such as music
  background.

Export checks should confirm that tapping trial rows, participant rows,
response/post-survey rows, and recording references are present and keyed to the
same stimulus ids used in the manifest.

For REPP exports, also inspect `analysis` and `output` JSON for marker counts,
marker timing error, raw and aligned tap counts, response-to-stimulus ratio,
asynchrony summaries, and `failed`/`reason`. With `sms_tapping`, REPP marks
trials failed when markers are missing, marker timing error is at least 15 ms,
raw taps are below 50% or above 150% of stimulus onsets, or valid asynchrony
statistics cannot be computed with at least 2 matched responses and SD above
10 ms.

## Validation and simulation

- Run a Python import smoke test when practical.
- Run `psynet test local` with bots that cover the ordinary success path and at
  least one calibration or failure branch.
- Inspect a browser/manual run to confirm that audio plays, recording permission
  works, progress stages match timing, and completion works.
- Record participant-flow evidence showing at least one calibration or practice
  trial and one main tapping trial.
- Export local or simulated data and verify tap onset fields, failure flags, and
  stimulus ids.
- Include an analysis script or notebook that summarizes valid trials per
  stimulus, taps per trial, inter-tap intervals, failed recordings, and coverage
  by condition or stimulus.

Useful simulated profiles include:

- good: enough taps, plausible inter-tap intervals, passes calibration;
- too-few-taps: fails a minimum-tap threshold;
- too-many-taps: fails a maximum-tap or quality threshold;
- off-tempo: taps at a wrong but internally stable period;
- noisy: high inter-tap variability;
- phase-shifted: stable taps consistently early or late;
- dropout: missing recording or incomplete trials.

Reports must state that simulated tapping validates workflow and analysis code,
not human rhythm perception.

## Public-safety rules

- Do not commit or publish private participant data, deployment logs, real app or
  server details, credentials, `cap.pem`, API keys, recruiter tokens, `.env`
  files, copyrighted audio, unreleased stimuli, raw private file paths, or
  identifiable participant metadata.
- Keep public examples self-contained with generated/demo audio and synthetic or
  clearly anonymized mock PsyNet-format data.
- If a real research pipeline uses ground truth, proprietary audio, or private
  exports, summarize reusable patterns only and keep the source material out of
  public skills and challenges.
