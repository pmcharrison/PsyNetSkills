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
- The audio pre-screen uses an embedded static WAV data URI generated locally
  with `espeak-ng` saying "five". I checked the local PsyNet demos and the
  public reference branch for reusable typed "five" screening assets; PsyNet
  provides reusable audio forced-choice and volume/headphone screening modules,
  but the public challenge specifically asks for typed `five`/`5` validation,
  so this attempt uses a small custom page. The WAV is embedded in
  `experiment.py` rather than committed as `five.wav`, because this repository
  stores WAV files through Git LFS and missing LFS objects make browser playback
  fail in ordinary clones.

## Running locally

```bash
cd challenges/rolling-inventory-melody-market/attempts/2026-06-10-20-01/code/rolling_inventory_melody_market
python3 experiment.py
psynet test local
```
