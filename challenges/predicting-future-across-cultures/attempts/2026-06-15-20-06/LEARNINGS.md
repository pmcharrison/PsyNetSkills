# Learnings

## Locale evidence runs need explicit locale precedence

When one PsyNet experiment is run repeatedly for locale-specific evidence, helper code should prefer an explicit evidence-run environment variable before falling back to deployment metadata. Otherwise a stale deployment locale can cause exports or assertions to report the wrong language.

*Actions:*

- **PsyNetSkills:** Add a note to the translation/evidence guidance recommending that locale-specific evidence helpers prefer the explicit run locale (for example `PSYNET_LOCALE`) before `get_locale()` when the same local deployment workflow is reused across languages. Confidence: medium. Impact: medium. Status: considering.

## Validation modals must be dismissed in Playwright evidence scripts

PsyNet validation failures can appear as modal dialogs with locale-specific acknowledgement buttons. Evidence scripts that intentionally trigger validation should screenshot the error and then dismiss the modal before correcting the answer.

*Actions:*

- **PsyNetSkills:** Add a validation-modal reminder to `record-participant-video` so Playwright evidence scripts include locale-aware dismissal after expected validation failures. Confidence: high. Impact: low. Status: considering.
