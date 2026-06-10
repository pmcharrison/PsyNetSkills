# Learnings

## PsyNet translation extraction needs gettext

`psynet translate` shells out to `xgettext` for Python extraction. The Cursor
Cloud image used for this attempt did not have the `gettext` package installed,
so the first extraction run failed before installing it.

*Actions:*
- **PsyNetSkills:** Add `gettext`/`xgettext` to the repository's documented
  Cursor Cloud system dependencies for translation-focused work. Confidence:
  high. Status: considering.

## Translation attempts need to check framework-owned pages

The experiment trial text was translated, but video review caught English text
on the built-in PsyNet/Dallinger finish button and final recruiter exit page.
Translation attempts should explicitly inspect framework-owned consent, debrief,
and completion pages, not only custom trial pages.

*Actions:*
- **PsyNetSkills:** Add a reminder to `prepare-for-translation` or challenge
  evidence guidance to inspect framework-owned participant pages during
  translation attempts. Confidence: high. Status: completed. Notes: Added to
  `prepare-for-translation`.
