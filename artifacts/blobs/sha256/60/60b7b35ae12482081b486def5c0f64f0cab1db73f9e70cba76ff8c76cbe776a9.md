# Audio memory sequence

This PsyNet experiment asks participants to listen to four short tone sequences
and reproduce each sequence using Low, Medium, and High buttons.

The WAV files are synthesized from sine tones by `generate_stimuli.py` using the
deterministic manifest in `data/sequences.json`. They can be regenerated with:

```bash
python generate_stimuli.py
```

Run local validation from this directory with:

```bash
psynet test local
```
