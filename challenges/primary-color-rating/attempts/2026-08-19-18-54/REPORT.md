# Report

## What was implemented

A nested PsyNet experiment at `code/primary_color_rating/` shows a welcome page,
then three `StaticTrial`s (red, green, blue) with `ColorPrompt` and a 1–7
`RatingControl` for pleasantness, then a thank-you page. One rating is stored
per color (`answer` is `{"rating": n}`; the export also has a `rating` column).

Scaffolding used `psynet setup --psynet-source editable` against `~/PsyNet`.
Human plan review was skipped because this is a workflow dogfood run.

## Commands run

- `python experiment.py` (import/smoke)
- `psynet test local` — **passed** after fixing the bot assertion for dict answers
- `psynet simulate` — **passed**; export at `data/simulated_data/`
- `psynet performance-test local --n-bots 4 --duration-minutes 1 --audit <attempt>`
  — smoke, not a 40-bot/5-minute production load test
- Brief `psynet debug local --no-browsers --legacy` to capture
  `artifacts/monitor.html` from `/dashboard/data`

## Evidence

- `logs/psynet_test_local.log`
- `logs/psynet_simulate.log`
- `logs/psynet_performance_test.log`
- `artifacts/simulated_data.zip` — 8 bots × 3 colors = 24 trials
- `analyses/analysis.ipynb` — executed; each participant has one 1–7 rating per color
- `artifacts/performance.json` — 1-minute / 4-bot smoke
- `artifacts/monitor.html` — authenticated Basic data dashboard snapshot (password redacted)

## Analysis

Simulated bots choose ratings at random. The notebook only checks structure:
eight participants, three colors, one rating each in 1–7. Mean ratings are not
scientific conclusions.

## Blocked / missing

- `artifacts/participant.mp4` — no headed Playwright participant recording in this
  dogfood run. Next: follow `record-participant-video`.
- Screenshot walkthrough — not captured; not required.

## PsyNet checkout

Did not check out `origin/master`. That revision has no `psynet audit` CLI.
The attempt used `~/PsyNet` branch `cursor/extensible-audit-profile-75f9` at
`4c6cab6af352d7a1ca17a6616bab7f5a074a53b6` (`13.4.0a0`).

## How to reproduce

From `code/primary_color_rating/` with PostgreSQL and Redis running:

```bash
source .venv/bin/activate
psynet test local
psynet simulate
```
