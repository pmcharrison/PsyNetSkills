# Rolling inventory melody market

This PsyNet experiment reimplements the rolling-inventory market paradigm from
the reference drawing task using short melodies as the artefact domain.

## Preserved reference mechanics

- 32 across-participant imitation chains, alternating popularity-information
  (`pi`) and no-popularity (`npi`) conditions.
- Eight trials per participant.
- One creator per generation.
- Rolling inventory capacity of 12 items.
- Adoption begins after the first inventory item exists.
- Market ancestry, proposal counts, adoption counts, condition assignment, and
  interaction metadata are recorded in trial answers and control metadata.

## Music-domain changes

The original drawing task used a 16 by 16 binary grid with 24 edits for adopted
items and 32 edits for seed creations. The melody editor has only nine time
slots, so the edit limits are scaled to the domain:

- from scratch: up to nine note changes, allowing any slot to be filled;
- adopted melody: up to three note changes, preserving a stricter edit regime.

Melodies are stored as a nine-item list. `null` is a rest, `0` is Do, `1` is Re,
and `2` is Mi.

## Local validation

Run from this directory in the PsyNet virtual environment:

```bash
python experiment.py
psynet test local
psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output ../../evidence/performance.json
```
