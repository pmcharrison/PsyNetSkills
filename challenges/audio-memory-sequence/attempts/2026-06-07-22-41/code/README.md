# Audio memory sequence

Run the PsyNet experiment from the nested package directory:

```bash
cd audio_memory_sequence
psynet test local
```

The nested directory avoids a Dallinger import collision with Python's standard
library module named `code`.

For short visual review runs, set `PSYNET_PROFILE=minimal` before launching
`psynet debug local`. The minimal profile keeps the custom sequence-recall flow
but reduces the participant-facing trial count to two and displays a review-mode
notice.

For fast full-flow review recordings, launch the experiment normally and run:

```bash
python scripts/playwright_participant_flow.py "<participant-url>"
```

The scripted runner drives the same participant UI as a human reviewer and is
intended to be used with screen/audio recording.
