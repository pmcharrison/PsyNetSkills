# Report

## Implementation summary

The attempt implements a self-contained PsyNet experiment in `code/cross_cultural_animal_choice/`. Participants see a welcome page, an instruction page, two animal-choice trials, and a thank-you page. Each trial presents cat, dog, and bird simultaneously using local SVG icons, text labels, and keyboard hints. The trial order is fixed to the two approved prompts, while the animal order is randomized independently on each trial.

Responses are stored as structured trial answers containing the prompt key, English prompt text, randomized animal order, selected animal, response position, locale, browser platform, and reaction time. The experiment also defines `get_basic_data()` so exports include flattened trial and participant tables for analysis.

## Translation readiness

All participant-facing text in `experiment.py` is marked with PsyNet's translation helper using `get_translator(namespace="experiment")`. The source locale is configured as English in `config.txt`, with no target locales declared yet. Running `psynet translate` generated `locales/experiment.pot` successfully and extracted 12 expected participant-facing strings, including both prompts and the three animal labels. No real translation API credentials were configured.

## Analysis

`analysis.py` reads exported or simulated trial data, computes choice counts and proportions by prompt, locale, and selected animal, and writes `evidence/analyses/choice_proportions.csv`. It can also produce a bar plot when `matplotlib` is available.

## Evidence summary

- `evidence/participant.mp4` shows the participant flow through the welcome page, instructions, two randomized animal-choice trials, and thank-you page.
- `evidence/screenshots/` contains targeted Playwright screenshots with a manifest.
- `evidence/performance.json` records a 40-bot, 5-minute local performance test with 0 bot errors and 0 request errors.
- `evidence/data.zip` contains a local PsyNet export.
- `evidence/monitor.html` contains an authenticated dashboard monitoring snapshot.

## Validation summary

The experiment passed `python experiment.py`, `psynet translate`, `psynet test local`, `psynet simulate`, the analysis script on simulated data, the scripted Playwright participant flow, and the standard PsyNetSkills validation/build checks. During performance testing, the load test started 298 bots over 5 minutes; 260 completed successfully, 37 were still running when the fixed-duration test ended, 1 never reached the database, and no bot or request errors were reported.
