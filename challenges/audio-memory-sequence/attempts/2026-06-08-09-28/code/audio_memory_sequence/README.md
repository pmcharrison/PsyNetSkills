# Audio memory sequence

PsyNet experiment for the audio-memory-sequence challenge attempt.

## Stimulus synthesis

Tones are synthesized in the browser with PsyNet's `JSSynth` helper rather than
pre-recorded audio files. Three MIDI pitches map to the labels:

- Low: 55
- Medium: 60
- High: 65

Trial sequences are defined deterministically in `trials_manifest.json`, which
can be regenerated with:

```bash
python generate_trials.py
```

## Local commands

From this directory, with the PsyNet virtual environment active:

```bash
uv pip install -r constraints.txt
psynet test local
psynet debug local
psynet performance-test local --output performance.json
```
