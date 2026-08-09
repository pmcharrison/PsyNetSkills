# Adaptive musical preference experiment

This PsyNet experiment estimates musical preference with adaptive pairwise
choices. Each synthesized clip varies in tempo and timbral brightness. The task
uses an MCMCP chain: each trial compares the current chain state with a nearby
proposal, and the participant's preferred clip becomes the next state.

## Run

```bash
python experiment.py
psynet test local
python analysis.py --simulate --output ../../evidence/analyses/simulated-summary.json
```

The exported data path can be summarized with:

```bash
python analysis.py --data-zip ../../evidence/data.zip --output ../../evidence/analyses/export-summary.json
```
