# Plan

## Science

This compact demonstration tests the mechanics of a tapping-to-beat experiment rather than making claims about human rhythm perception. Generated click tracks provide stable public-safe rhythmic stimuli, and deterministic simulated tapping profiles exercise the data path and analysis code.

## Methods

Participants first read a short introduction explaining that the study uses simple generated tones and that they should tap a button in time with the beat. A representative volume-check click track verifies audible playback. Participants then complete a calibration trial with an isochronous metronome; calibration requires enough taps, a mean inter-tap interval near the target beat interval, and limited timing variability. Only participants with usable calibration proceed to three short main tapping trials spanning slow, medium, and accented metronome conditions. Each trial saves stimulus id, condition, timing constants, generated audio filename, tap onset times relative to audio prompt start, tap counts, inter-tap interval summaries, calibration status, failure flags, failure reasons, and the simulated profile id when applicable.

Five deterministic bot profiles cover the required paths: `good`, `too-few-taps`, `off-tempo`, `noisy`, and `dropout`. The good profile passes calibration and completes the main trials. The other profiles produce calibration records with distinguishable failure reasons and exit before the main task, preserving the rule that the main task requires usable calibration.

## Implementation

The experiment lives in `code/tapping_rhythm_experiment/` and uses PsyNet static trials with a custom `TimedPushButtonControl` subclass. Stimuli are generated WAV click tracks from stdlib Python and recorded in `stimuli/manifest.json`; no private or copyrighted audio is used. The control formats both browser and bot responses from PsyNet event logs, so simulated taps exercise the same tap-onset parser as participant clicks. Bot profile assignment happens in `Exp.initialize_bot`, and `Exp.test_check_bot` asserts expected pass/fail behavior. Evidence includes `psynet test local`, `psynet simulate`, export checks, performance evidence where runnable, Playwright-driven participant screenshots/video, a canonical executed notebook, and `REPORT.md`.
