---
score:
---

# Evaluation

## Summary

Summarize the human evaluator's overall judgment.

## Strengths

- 

## Weaknesses

- 

## Criteria

No private criteria were supplied for this challenge.

## Evidence notes

- `code/` contains the runnable PsyNet experiment and generated placeholder
  stimulus set. Target placeholders are neutral/50-50 faces; happy/angry target
  codes are retained only for counterbalancing and congruency analysis.
- `evidence/participant.mp4` records the participant flow from the landing page
  through final completion using a scripted browser runner at 30 fps. The
  experiment is visual, so the recording has no audio stream.
- `evidence/performance.json` records a 40-bot, five-minute local performance
  test with zero bot failures.
- `evidence/monitor.html` contains a local PsyNet dashboard snapshot.
- `evidence/data.zip` contains anonymized exported PsyNet CSV tables from the
  local bot/performance run.
- `evidence/exported_trial_records.json` and
  `evidence/analyses/priming_summary.csv` summarize completed trial records.
- A first export attempt to write directly outside the experiment directory
  failed on local path permissions after producing database-export output. The
  final export used an in-experiment path plus `--no-source`, then packaged the
  anonymized CSVs into the required evidence zip.

## Notes

- Score and feedback should come from a human evaluator, captured
  conversationally when working with Cursor Cloud Agents.
