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
  audio pre-screening outcomes are recorded.

## Music-domain changes

The original drawing task used a 16 by 16 binary grid with 24 edits for adopted
items and 32 edits for seed creations. The melody editor has only nine time
slots, so the edit limits are scaled to the domain:

- from scratch: up to nine note changes, allowing a participant to fill slots
  or add overlapping notes;
- adopted melody: up to three note changes, preserving a stricter edit regime.

Melodies are stored as a nine-item list. Each time slot stores a list of active
pitches; an empty list is a rest, `0` is Do, `1` is Re, and `2` is Mi. Multiple
pitches in the same slot are overlapping notes.

Participants complete an audio pre-screening page after consent and before the
main task. The page plays a committed static voice clip saying "five" and asks
participants to type what they heard. Incorrect responses route to PsyNet's
unsuccessful end branch with `performance_check` and `audio_pre_screening`
failure tags, matching PsyNet prescreen patterns used by recruiter/payment
integrations.

I checked the accessible Computational Audition Lab GitLab repositories for
audio pre-screening patterns. Group-wide blob search was unavailable to this
agent, and project-level searches did not identify a reusable audio
pre-screening implementation that was clearly more robust than the challenge's
baseline static "five" repeat-back check. The attempt therefore uses the
baseline static voice clip and documents the PsyNet failure-tag routing.

The reference drawing task's mouse movement tracking, stroke event tracking,
and drawing-specific interaction logs are intentionally omitted.

## Local validation

Run from this directory in the PsyNet virtual environment:

```bash
python experiment.py
psynet test local
psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output ../../evidence/performance.json
```
