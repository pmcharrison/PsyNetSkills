# Private evaluation criteria

Use these criteria when evaluating an attempt. Award credit for compact,
public-safe work that demonstrates a real local PsyNet tapping workflow rather
than for building a large production study.

## Required implementation

- The attempt implements a runnable PsyNet experiment with audio playback,
  calibration or practice, and main tapping trials.
- Audio stimuli are generated tones, clicks, metronomes, or similarly
  public-safe synthetic assets. The attempt does not use copyrighted recordings,
  private data, private paths, real deployment details, recruiter credentials, or
  production service secrets.
- The participant flow is small and reviewable, with clear start/stop cues and
  saved tap onset data.
- Timing constants and generated-stimulus metadata are explicit enough to connect
  stimulus ids, target beat timing, response windows, and analysis code.

## Simulated profiles

- The attempt includes all required profiles: `good`, `too-few-taps`,
  `off-tempo`, `noisy`, and `dropout`.
- Profile ids are visible in exported participant or trial metadata.
- Profiles exercise real experiment response formatting, trial persistence,
  calibration status, and failure flags rather than bypassing the experiment with
  a detached fake dataset.
- The `good` profile produces valid trials, while each failing or edge profile
  produces the expected failure, anomaly, or incomplete-data pattern.

## Export and validation

- Local simulated runs produce exportable PsyNet-format data or a clearly
  justified equivalent derived from the local PsyNet run.
- Export checks verify participant rows, trial rows, stimulus ids, tap onset
  fields, calibration status, failure flags, and failure reasons.
- Trial rows include both calibration/practice and main tapping trials.
- Stimulus ids in exported rows match the generated-stimulus manifest or
  equivalent metadata.
- Tap onset fields are present, parseable, and tied to the correct participant,
  trial, and stimulus.
- The dropout profile is distinguishable from ordinary failed tapping trials.

## Analysis and report

- The analysis notebook or script runs on the exported or documented simulated
  PsyNet-format data.
- The analysis summarizes taps per trial, inter-tap intervals, valid and failed
  trials, calibration outcomes, failure flags, and coverage by simulated profile.
- Analysis outputs are concise and reviewable, with small tables or plots where
  useful.
- `REPORT.md` states that simulated tapping validates workflow and analysis code,
  not human rhythm perception.
- `REPORT.md` accurately describes the experiment, generated audio, simulated
  profiles, export checks, analysis results, and remaining limitations.

## Evidence quality

- Participant-facing evidence shows audio playback, calibration or practice, and
  at least one main tapping trial.
- Evidence and logs avoid secrets, private paths, real recruitment details, and
  unpublished or proprietary assets.
- `agent.json`, `TIMELINE.md`, and `LEARNINGS.md` are present and consistent with
  the attempt evidence.
