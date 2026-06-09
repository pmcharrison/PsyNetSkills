---
name: prepare-for-translation
description: An experimental skill to prepare an existing PsyNet experiment for translation by marking participant-facing text, updating locale configuration, validating extraction, and committing the result.
authors: [pmcharrison]
---

# Prepare for translation

Use this skill when the user asks you to make a PsyNet experiment translatable
or ready for `psynet translate`.

## Required reads

- Read PsyNet's internationalization documentation, currently
  `~/PsyNet/docs/tutorials/internationalization.rst`.
- Inspect the translation demo
  (`demos/experiments/translation/experiment.py`).
- Review the target experiment's `experiment.py`, templates, config files, and
  any custom pages/components before editing.

## Workflow

1. Identify every participant-facing string: instructions, headings, prompts,
   labels, button text, feedback, consent/ad copy, template text, formatted
   messages, custom JavaScript-visible text, and dynamically generated page
   content.
2. Add `from psynet.utils import get_translator` where needed, then define
   `_ = get_translator()` at module scope. If context is genuinely needed for
   ambiguous strings, also define `_p = get_translator(context=True)`.
3. Mark translatable literals with direct extractor-visible calls:
   `_("Text")` for ordinary strings and `_p("context", "Text")` for contextual
   strings. Do not rename `_` or `_p`, wrap them in helper functions, or pass a
   variable instead of a literal string.
4. Replace f-strings and string concatenation used for user-facing text with
   translator literals plus `.format(...)`, for example
   `_("Hello, {NAME}!").format(NAME=name)`. Use uppercase placeholder names with
   underscores only.
5. Keep translation units short and natural. Prefer separating page structure
   from text with `dominate.tags`; avoid embedding HTML tags inside strings
   that translators will edit.
6. Update experiment configuration so `psynet translate` knows the intended
   locale set. Add or update `locale` and `supported_locales` in the experiment
   config or `config.txt`; include English plus each requested target locale.
   If older code uses `language`, align it with current PsyNet documentation or
   migrate it to `locale` rather than adding stale duplicate settings.
7. Before relying on automatic translation, confirm the active PsyNet checkout is
   recent enough to include the Autotranslation work (commit
   `02a1cdded737d9fae294b789f7d5a5c288d59580` or a later `master`/release).
   Update the local PsyNet checkout when appropriate, or record the version
   blocker if the environment cannot be updated.
8. Run the strongest safe validation available from the experiment directory:
   usually `psynet translate <locale>` when local/test translation credentials
   or a mock translator are available, otherwise run an extraction/check path
   that creates `locales/experiment.pot` without real service credentials.
   Also run the experiment's existing tests or `psynet test local` when the
   change affects participant flow.
9. Inspect the generated POT/PO entries or command output to confirm every
   marked string was extracted and no f-string-resolved English text remains.
10. Commit the code/config/test changes. The skill's output is an applied,
   committed experiment change, not a report that lists what the user should do.

## Rules

- Never write `_(f"...")`, `_("{value}")` with lowercase placeholders, or
  `_("... " + value)`. PsyNet's extractor must see the literal English message
  at compile time.
- Do not configure real OpenAI, Google, Prolific, AWS, or other production
  credentials. If translation APIs are unavailable, still prepare the code and
  document the exact validation blocker.
- Keep translator API settings such as `.dallingerconfig`, OpenAI API keys, and
  Google Translate JSON paths machine-local and uncommitted. Do not retrieve,
  copy, or publish credentials from private stores as part of this skill.
- Do not translate non-participant identifiers such as page labels, trial IDs,
  asset filenames, data keys, model names, or analysis-only strings unless they
  are displayed to participants.
- Preserve existing meaning and experiment logic. Translation preparation should
  not redesign the task or change scoring, trial order, or data schemas unless a
  text path cannot be made translatable otherwise.
