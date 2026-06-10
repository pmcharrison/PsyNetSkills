# Evaluation criteria

An implementation should be judged successful if it satisfies the following
criteria.

## Translation preparation

- Starts from PsyNet's static demo at `~/PsyNet/demos/experiments/static` and
  preserves the original static-trial task behavior.
- Uses PsyNet's translation conventions consistently, including
  `_ = get_translator()` and direct `_("<text>")` or contextual `_p(...)`
  markers for participant-facing strings.
- Does not use f-strings, string concatenation, or renamed translation wrappers
  for translatable participant-facing text.
- Updates `locale` and `supported_locales` in the experiment configuration so
  that Spanish (`es`) is supported and can be selected as the active locale.

## Spanish translation

- Runs `psynet translate` for Spanish from the experiment directory and commits
  the generated `locales/es/LC_MESSAGES/experiment.po` file and related
  translation template/output files.
- Provides evidence that the participant-facing experiment runs in Spanish
  after the Spanish locale setting is applied.
- Translates the complete participant interface, including instructions,
  prompts, response options, buttons or labels controlled by the experiment,
  feedback, and completion text.
- Does not include real or custom translation-service credentials in code,
  configuration, logs, or evidence.

## English regression check

- Demonstrates that changing the locale back to English restores the original
  English participant-facing interface.
- Shows that translation preparation did not alter trial order, stimuli,
  response collection, scoring, or saved-data semantics.
- Includes enough comparison evidence to verify that the English interface is
  unchanged except for non-visible translation plumbing.

## Evidence

- Includes command output or logs showing successful translation extraction and
  Spanish translation generation.
- Includes participant-facing evidence for the Spanish run and the English
  regression run.
- Records any environment limitation honestly if translation-service access is
  unavailable, while still showing that extraction and locale configuration were
  prepared correctly.
