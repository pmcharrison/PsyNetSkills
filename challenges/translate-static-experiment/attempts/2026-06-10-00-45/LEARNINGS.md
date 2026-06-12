# Learnings

## PsyNet translation extraction needs gettext

`psynet translate` shells out to `xgettext` for Python extraction. The Cursor
Cloud image used for this attempt did not have the `gettext` package installed,
so the first extraction run failed before installing it.

*Actions:*
- **PsyNetSkills:** Add `gettext`/`xgettext` to the repository's documented
  Cursor Cloud system dependencies for translation-focused work. Confidence:
  high. Impact: low. Status: completed. Notes: Added to `AGENTS.md`.
## Translation attempts need to check framework-owned pages

The experiment trial text was translated, but video review caught English text
on the built-in PsyNet/Dallinger finish button and final recruiter exit page.
Translation attempts should explicitly inspect framework-owned consent, debrief,
and completion pages, not only custom trial pages.

*Actions:*
- **PsyNetSkills:** Add a reminder to `prepare-for-translation` or challenge
  evidence guidance to inspect framework-owned participant pages during
  translation attempts. Confidence: high. Impact: high. Status: completed. Notes: Added to
  `prepare-for-translation`.
- **PsyNet:** Make framework-owned debrief, finish-button, recruiter-exit, and
  completion-page text participate in experiment translation without requiring
  per-experiment monkey patches or template overrides. Confidence: high. Impact: high. Status:
  considering.
## Right-to-left language rendering needs framework-level testing

The evaluator translated the experiment locally into additional languages with
valid translation credentials. Hebrew translation exposed right-to-left and
logical-Hebrew rendering issues. The evaluator judged this as likely originating
in PsyNet's translation/rendering layer rather than in the attempt-specific
experiment code.

*Actions:*
- **PsyNet:** Add regression coverage and rendering support for right-to-left
  locales such as Hebrew, including participant-facing trial pages and
  framework-owned completion pages. Confidence: medium. Impact: high. Status: considering.
