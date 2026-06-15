# Plan

## Science

This experiment reimplements the everyday prediction task from Griffiths and Tenenbaum (2006) as a concise PsyNet survey. Participants observe a partial duration or extent, `t_past`, and predict the total value, `t_total`. The main design goal is not to estimate real cultural differences, but to produce a multilingual experiment and simulated dataset that can show condition-by-language patterns when such patterns are injected by bots.

The visible challenge reference folder currently contains only `references/README.md`, not the attached PDF described in the public instructions. Unless the PDF becomes available before implementation, the participant vignettes will be adapted conservatively from the public prompt bases and the limitation will be documented in `REPORT.md` and `EVALUATION.md`.

## Methods

Participants complete five prediction trials, one from each category:

- life spans: `t_past` in 18, 39, 61, 83, or 96 years;
- marriage lengths: `t_past` in 1, 3, 7, 11, or 23 years;
- movie run times: `t_past` in 30, 60, 80, 95, or 110 minutes;
- poem lengths: `t_past` in 2, 5, 12, 32, or 67 lines;
- waiting times: `t_past` in 1, 3, 7, 11, or 23 minutes.

For each participant, the category order will be randomized and one `t_past` value will be sampled uniformly within each category. Each trial will show a short vignette, the observed value so far, and a numeric input for the predicted total value. Participants will be told to answer intuitively rather than by calculation. Validation will reject non-numeric values and finite predictions smaller than the displayed `t_past`; retry information will be saved for quality control.

The exported data will include category, vignette identifier, `t_past`, unit, displayed locale, numeric prediction, whether the prediction is finite, reaction time, validation failure count or messages, and bot profile metadata for simulated runs. The end page will debrief participants that the study concerns everyday prediction under uncertainty.

The participant-facing language set will be English (`en`), Italian (`it`), and Hebrew (`he`). Hebrew pages will include right-to-left presentation cues where custom participant-facing layout is under experiment control. Because challenge attempts must not use real translation-service credentials, target-language `.po` files will be written or completed locally and `psynet translate it he` will be used for extraction and consistency checks without relying on external translator APIs.

## Implementation

The runnable experiment will live in `code/predicting_future_across_cultures/` to avoid making `code` itself the Dallinger import package. It will include standard PsyNet support files such as `experiment.py`, `config.txt`, `constraints.txt`, `.gitignore`, and locale files.

The implementation will use PsyNet's timeline and modular page APIs:

- `InfoPage` for instructions and debrief;
- `PageMaker` or a timeline-building function to generate each participant's randomized five-trial sequence;
- `ModularPage` with `NumberControl` for the prediction response;
- a small custom page or validation layer if `NumberControl` alone cannot enforce `prediction >= t_past` while recording retries cleanly;
- participant variables or trial-level saved metadata to preserve locale, category, `t_past`, unit, vignette id, bot profile, and validation telemetry.

Participant-facing strings will be marked with `from psynet.utils import get_translator` and `_ = get_translator()` at module scope. Dynamic text will use extractor-visible literals with uppercase `.format(...)` placeholders, for example `_("The man is currently {T_PAST} years old.").format(T_PAST=t_past)`. Trial definitions will store stable language-neutral identifiers and numeric values; translated strings will be resolved at render time so database records do not freeze the wrong locale.

The configuration will keep translation settings in one place, preferably `config.txt`, with source locale `en` and `supported_locales = ["en", "it", "he"]`. The implementation will avoid real credentials, real recruiter services, and personally identifying participant prompts.

Simulated participants will use profile-specific response functions that always return finite `t_total >= t_past`. Profiles will vary modestly by locale, for example:

- English: baseline slope and offset by category;
- Italian: slightly higher predictions for marriage and waiting-time categories;
- Hebrew: slightly higher life-span and movie-runtime predictions and lower poem-length predictions.

The simulation will record profile id, locale, random seed, and category parameters so the notebook can distinguish injected simulation patterns from real human behavior.

## Validation and evidence plan

After human approval of this plan, implementation will be validated with:

- `python experiment.py` from the experiment directory;
- `psynet translate it he` plus inspection of `locales/experiment.pot` for expected strings;
- `psynet test local` with bots covering ordinary and validation-edge responses;
- browser participant-flow evidence for at least English, Italian, and Hebrew, saved under `evidence/screenshots/` and `evidence/participant.mp4`;
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output <absolute evidence path>`;
- `psynet simulate` with enough participants per locale to populate all category-by-language panels;
- `evidence/simulated_data.zip`;
- an executed `evidence/analyses/analysis.ipynb` that reads exported CSV data directly, shows summary tables, and plots `t_past` against finite predicted `t_total` faceted by category and language;
- `REPORT.md` summarizing implementation, validation, simulation, analysis, translation readiness, limitations, and any blockers.

## Human review questions

Before implementation starts, please review:

1. Whether the public prompt bases are sufficient if the referenced Griffiths and Tenenbaum PDF remains unavailable in `references/`.
2. Whether the proposed locale-specific bot variations are acceptable as modest simulated differences.
3. Which GitHub username should be credited in `agent.json` as the human author for this attempt.
