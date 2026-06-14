# Rolling inventory melody market

This attempt reimplements the rolling-inventory drawing market from
`computational-audition-lab/niche-lucas` branch
`rolling-inventory-replication` as a melody-creation experiment.

Reference commit inspected: `617c9893cc78041552f46382e974cf364e3dbecb`.

## What is preserved

- 32 imitation chains, alternating popularity-information (`pi`) and
  no-popularity-information (`npi`) participant groups.
- 8 create/adopt rounds per participant.
- Rolling inventory size of 12 proposals.
- One creator per generation and 84 generations per chain.
- Adoption enablement once the market contains at least one melody.
- Ancestry, proposed-to counts, adopted-by counts, and participant condition
  metadata.

## Melody-specific changes

- Grid drawing is replaced by a 3 x 9 step sequencer with rows `Mi`, `Re`, and
  `Do`.
- Market items are previewed with audio playback buttons and small waveform
  summaries; the note grid is not shown in adoption.
- Creation uses WebAudio synthesis for preview and submission-time playback.
- The original mouse movement, stroke, and drawing-specific event logs are not
  recorded.
- The original typed `five` audio check was removed after adding a simple
  sound-only prescreening sequence. This avoids depending on a `five.wav` file,
  which is fragile in ordinary clones because this repository stores WAV files
  through Git LFS.

## Pre-screening choices

I inspected the referenced CAL experiments and copied the pieces that match this
experiment's listening-only requirements:

- `melcon-in` / `melodic-consonance` use a warning, volume calibration, and
  headphone test before a music-listening task. This task does not require
  headphones, so this attempt keeps the useful `VolumeCalibration` step but
  replaces headphone screening with an easy browser-generated sound check:
  participants hear three tones and identify the higher-pitched one.
- `gap/gap-draft` uses a role-aware audio test plus microphone checks. The
  microphone-specific parts are not copied because this task does not record
  speech.
- Singing and tapping readiness experiments add microphone, recording/playback,
  tapping, or singing calibration. These are intentionally not copied because
  they would screen for abilities that are irrelevant to composing a step
  sequencer melody.
- The forced-choice custom headphone gate uses hand-rolled JavaScript and remote
  antiphase assets. This attempt does not copy that gate because it would
  require headphones and is stricter than the melody market needs.

## Running locally

```bash
cd challenges/rolling-inventory-melody-market/attempts/2026-06-10-20-01/code/rolling_inventory_melody_market
python3 experiment.py
psynet test local
```
