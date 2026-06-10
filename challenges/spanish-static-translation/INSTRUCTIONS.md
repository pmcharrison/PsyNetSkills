---
title: Spanish translation of the static demo
type: experiment implementation
difficulty: 4
authors: [jacobyn]
---

Create a translatable Spanish variant of PsyNet's static demo, starting from
`~/PsyNet/demos/experiments/static`.

Use the `prepare-for-translation` skill as the workflow for preparing the demo.
The submitted experiment should be a runnable copy or adaptation of the static
demo in the attempt directory, not a patch to the shared PsyNet checkout. It
should preserve the original task logic while making participant-facing text
available to PsyNet's translation system.

The implementation should:

- Identify all participant-facing strings in the static demo, including
  instructions, prompts, labels, response options, feedback, and completion text.
- Mark translatable strings with PsyNet translation markers, using
  `_ = get_translator()` and direct extractor-visible `_("<text>")` calls where
  appropriate.
- Avoid f-strings for translatable text. When participant-facing text needs
  variables, use literal translation strings with uppercase `.format(...)`
  placeholders.
- Configure the experiment so that Spanish is available as a supported locale
  and the primary run setting uses Spanish, for example with `locale = es` or
  the equivalent experiment `config`.
- Run `psynet translate` for Spanish from the experiment directory so that the
  Spanish translation files are generated and committed with the attempt.
- Keep all translation API keys, Google Translate JSON files, `.dallingerconfig`
  secrets, and other credentials out of the submitted code and evidence.

The participant-facing result should run entirely in Spanish when the experiment
locale is Spanish. The experiment should also be easy to switch back to English,
and doing so should leave the original English participant interface unchanged
apart from the translation-enabling code.
