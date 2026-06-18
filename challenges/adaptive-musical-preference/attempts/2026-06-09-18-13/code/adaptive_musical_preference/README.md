# Adaptive musical preference

This PsyNet experiment estimates a participant's preferred region in a two-dimensional synthesized music space:

- `tempo`: beats per minute of a short arpeggiated pattern.
- `brightness`: strength of upper harmonics in the synthesized tone.

Each trial plays Option A followed by Option B. The underlying MCMCP chain compares the current preferred state with a nearby proposal; the participant's choice becomes the current state for the next pairing. Trial definitions store the current state, proposal, randomized option order, and the finalized answer stores the chosen option, role, and stimulus parameters.

Run locally from this directory with:

```bash
psynet test local
```

Summarize simulated or exported data with:

```bash
python analysis.py [path/to/data.zip]
```
