# Report

## Methods

This attempt implements a compact PsyNet tapping experiment with generated click-track WAV stimuli only. The participant flow includes an introduction, representative volume check, isochronous calibration trial, calibration gate, three main tapping trials, and a successful completion path. Taps are collected with an on-screen timed button and saved as onset times relative to PsyNet's audio prompt start event.

## Implementation

The runnable experiment is in `code/tapping_rhythm_experiment/`. Stimulus metadata lives in `stimuli/manifest.json`, and `generate_stimuli.py` can regenerate the public-safe audio files. The custom `TapButtonControl` formats browser and bot event logs through the same tap-onset parser. Simulated profile metadata is written to participant variables and each tapping trial answer.

## Simulation and export

`psynet test local` passed with five deterministic profiles: `good`, `too-few-taps`, `off-tempo`, `noisy`, and `dropout`. `psynet simulate` produced `evidence/simulated_data.zip`; `evidence/export_checks.py` verified participant rows, tapping trial rows, manifest stimulus ids, tap onset fields, calibration status, failure flags, failure reasons, and a distinguishable dropout profile.

## Analysis

`evidence/analyses/analysis.ipynb` reads the simulated export directly and summarizes tap counts, inter-tap intervals, valid versus failed trials, calibration outcomes, failure reasons, and coverage by simulated profile. The notebook is executed in place and kept small for dashboard rendering.

## Participant evidence

`evidence/participant.mp4` shows the participant path through intro, volume check, calibration, main tapping trials, and completion. Audio is present in the MP4; `participant_volumedetect.txt` reports non-silent levels. `evidence/screenshots/` contains targeted screenshots with captions in `manifest.json`.

## Performance

`evidence/performance.json` records a five-minute local performance test with 40 concurrent bots, 2,937 requests, zero request errors, zero bot errors, median response time 0.119 s, and P95 response time 1.182 s. Some bots remained incomplete when the timed load window ended, which is expected for a fixed-duration replenishing load test and not recorded as bot errors.

## Limitations

These simulated tapping profiles validate workflow, export, and analysis code only. They do not validate human rhythm perception, perceptual timing accuracy, recruitment quality, or scientific conclusions about tapping behavior.
