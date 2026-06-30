# Plan

## Science

This experiment will demonstrate a translatable, cross-cultural decision-making task without making empirical claims about real cultural differences. Participants will repeatedly choose between two options that differ in small sets of interpretable features. The local implementation will use demonstration stimuli only; exported data will retain language-neutral stimulus identifiers and feature keys so that a later real study could compare choices across participant locale or recruitment context without storing translated display text as the analytic variable.

## Methods

The study will use a within-participant forced-choice design. On each trial, participants will see two options side by side. Each option will have a variable number of features, such as low effort, high reward, familiar source, or delayed payoff. The number and combination of features will vary across trials, and the side assignment of the two options will be randomized at render time where possible.

Participants will first see a short welcome page, then a full instruction page explaining that they should read both option cards and choose the option they would personally prefer. Each choice trial will repeat the core instruction on the same page as the options. After all trials, participants will see a short thank-you page. The experiment will save exactly one response per trial, including the selected side, selected option identifier, unselected option identifier, trial identifier, and locale-neutral feature keys for both options.

The task will be localized for English (`en`), Hindi (`hi`), and French (`fr`). Participant-facing text will be translated for evidence purposes, but stimulus definitions and exported analysis fields will remain stable English-like keys rather than translated prose. This keeps the demo suitable for cross-cultural workflow review while avoiding unsupported claims that the example translations or stimuli are validated for any cultural population.

## Implementation

The attempt code will live in `code/cross_cultural_decision_making/` to avoid importing a Python package named `code`. I will start from PsyNet's static-trial and translation demos rather than patching the shared PsyNet checkout. The experiment will use:

- `StaticNode` definitions for a compact set of option-pair trials.
- A custom `StaticTrial` subclass that renders two option cards and returns a `ModularPage`.
- `PushButtonControl` with two choices so one participant choice is saved per trial.
- A `StaticTrialMaker` configured for a short local run with all demo trials shown once per participant.
- A `Timeline` containing welcome, detailed instructions, the trial maker, and thank-you pages.
- `get_translator()` as `_` at module scope, with direct extractor-visible literals for participant-facing text.

Trial definitions will store stable fields such as `trial_id`, `left_option_id`, `right_option_id`, `left_features`, and `right_features`. Feature display labels will be resolved in `show_trial` from module-level translation dictionaries whose literals are visible to gettext. Dynamic text will use `.format(...)` with uppercase placeholder names only. I will avoid storing translated strings in node definitions because those records are serialized and should remain language-neutral.

Translation settings will be kept in `config.txt`, with `locale = en` for the source run and `supported_locales = ["en", "hi", "fr"]`. I will generate or maintain `locales/experiment.pot`, `locales/hi/LC_MESSAGES/experiment.po`, and `locales/fr/LC_MESSAGES/experiment.po` without using real translation API credentials. If PsyNet's translation command would call an external translator for missing entries, I will complete the `.po` files manually and then rerun extraction/consistency checks so the validation path remains credential-free.

## Validation and evidence plan

After implementation, I will run these checks from the experiment directory:

- `python experiment.py` to verify static stimulus definitions and package imports.
- `psynet translate hi fr` or the strongest credential-free extraction/consistency command available, then inspect `locales/experiment.pot` for the expected participant-facing strings.
- `psynet test local` to verify local participant flow and bot completion.
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output <absolute evidence path>` for performance evidence.
- `psynet debug local` plus Playwright-driven participant flows in `en`, `hi`, and `fr`.

Final evidence will include `evidence/participant.mp4` or separate concise videos showing the task running successfully in English, Hindi, and French, targeted screenshots of the welcome/instruction/trial/thank-you states, `evidence/performance.json`, `evidence/monitor.html`, and `evidence/data.zip`. Any blocked check will be recorded in `EVALUATION.md` rather than treated as passing.

## Human review questions

- Should the final evidence be one combined multilingual participant-flow video or three shorter locale-specific videos?
- Is the proposed compact static forced-choice design sufficient, or should the trial set include a specific decision-making construct such as risk, delay discounting, social allocation, or effort tradeoffs?
- Which GitHub username should be credited in `agent.json` as the human author before the attempt is completed?
