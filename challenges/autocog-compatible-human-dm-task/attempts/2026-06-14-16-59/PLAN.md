# Plan

## Science

The experiment will implement a configurable forced-choice decision task suitable for comparing feature-based choice strategies such as unweighted tallying and validity-weighted additive decision rules. The submitted example config contains binary option ratings and feature validities that can produce agreement, disagreement, and tie-like cases across these rules. The implementation will treat the rationale as design metadata only, and will preserve locale-neutral numeric ratings and validities in exported data so later analyses can compare participants across language conditions without relying on translated labels.

## Methods

The task will use a within-participant design. Each participant will first see a short welcome page and a full instruction page explaining that each decision involves two options described by the same fixed set of features. Each feature row will display the feature label, its validity from 0 to 1, and the numerical ratings for the two options. On every trial, the participant will choose the option they prefer. The choice page will repeat the core instructions so that participants do not need to remember the pre-task instructions.

Stimuli will be generated from an input Python dictionary named `config`. The number of features will be inferred from `len(config["validities"])`. Rating vectors in `trial_a_ratings` and `trial_b_ratings` will be paired by index and validated against the feature count. The trial sequence will repeat complete configured pairs until reaching the largest number of trials that is less than or equal to `max_trials`. Presentation order may be swapped trial by trial, but the paired A/B ratings will remain together. The experiment will save one choice per trial along with the trial index, source pair index, swap flag, validities, option A ratings, option B ratings, displayed left/right option identities, and selected option identity.

The generated participant-facing task will support English (`en`), Hindi (`hi`), and German (`de`). The local evidence will use demonstration translations only; it will not claim that the wording or stimuli are validated for any cultural population.

## Implementation

The attempt will live in `code/autocog_compatible_human_dm_task/` so PsyNet does not import a package named `code`. I will implement a small generator module rather than a one-off handwritten experiment:

- `example_config.py` will contain the supplied Python dictionary as `config`.
- `generate_experiment.py` will load a config module or file, validate it, build a self-contained generated experiment directory, and write files such as `experiment.py`, `config.txt`, `README.md`, and locale directories.
- The generated experiment will use PsyNet's static-trial pattern: `StaticNode` for generated trial definitions, a custom `StaticTrial` for rendering, and `StaticTrialMaker` for participant trial delivery.
- The generated trial renderer will use `dominate.tags` or similarly structured HTML rather than one large raw translated HTML string, so each visible phrase remains a natural translation unit.
- `PushButtonControl` will present two translatable button labels while saving language-neutral values such as `option_a` or `option_b`.
- `Exp.get_basic_data` will export reconstruction fields and choices in stable, language-neutral columns.

Config validation will reject missing keys, non-numeric validities, validities outside `[0, 1]`, unequal lengths of `trial_a_ratings` and `trial_b_ratings`, empty rating-pair lists, non-positive `max_trials`, and rating vectors whose lengths do not match `validities`. If `max_trials` is smaller than the number of configured pairs, the generator will include the first `max_trials` complete pairs. If `max_trials` is larger, it will repeat full cycles of all configured pairs up to the largest complete cycle not exceeding `max_trials`, as specified by the challenge.

Translation settings will be generated in `config.txt`, keeping `locale` and `supported_locales` out of the `Exp.config` dict to avoid duplicate PsyNet config registration. I will define `_ = get_translator()` and, if needed, `_p = get_translator(context=True)` at module scope. Participant-facing literals will be direct extractor-visible calls. Dynamic messages will use `.format(...)` with uppercase placeholders. The generator will produce non-fuzzy Hindi and German `.po` files manually for the demo strings so `psynet translate hi de` can run extraction and consistency checks without real translation credentials. Numeric ratings, validities, source pair indices, internal labels, and data keys will not be translated.

## Validation and evidence plan

After plan approval and implementation, I will validate both the generator and the generated experiment:

- Run a focused generator test or command that invokes `generate_experiment.py` on `example_config.py` and writes the generated experiment.
- Run config-validation checks for at least one malformed config, such as mismatched rating vector lengths.
- From the generated experiment directory, run `python experiment.py` to verify imports and generated static definitions.
- Run `xgettext --version` and `psynet translate hi de`, then inspect `locales/experiment.pot` for expected strings.
- Run `psynet test local` for local bot completion.
- Run `psynet simulate` with enough bots to produce a useful `evidence/simulated_data.zip`.
- Execute `evidence/analyses/analysis.ipynb`; the notebook will read exported CSVs directly, summarize choice proportions, and compare observed choices against tallying and WADD predictions computed from ratings and validities.
- Run `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output <absolute evidence path>`.
- Use `psynet debug local` and Playwright-driven participant flows to record concise videos in English, Hindi, and German.

Final evidence will include the generated experiment under `code/`, logs proving the generator produced it from the example config, multilingual participant-flow video evidence, targeted screenshots, `evidence/performance.json` or a documented blocker, `evidence/monitor.html`, `evidence/simulated_data.zip`, `evidence/analyses/analysis.ipynb`, and `REPORT.md`. Any command that cannot run because of the local environment will be recorded in `EVALUATION.md` with the exact blocker.

## Human review questions

- Should the generator include only the supplied example config, or should it also expose a documented CLI for arbitrary config files during review?
  - A: It should request the config file at the start of the skill implementation in CLI
- Should `max_trials` smaller than the number of configured pairs truncate the list to `max_trials`, or should that be treated as invalid because it does not use all configured pairs?
   - A: rpeat the pairs integer number of times such that total trials is always less than or equal to max trials
- Should feature labels be generic (`Feature 1`, `Feature 2`, ...) or should the config schema be extended to allow optional feature names?
  - Call it rating 1, 2, ...
