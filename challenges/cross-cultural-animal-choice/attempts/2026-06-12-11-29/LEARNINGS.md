# Learnings

## gettext must be present before translation extraction

`psynet translate` failed until the Ubuntu `gettext` package provided `xgettext`, even though the Python environment was otherwise ready. Installing `gettext` unblocked POT generation and verified the experiment's translation-ready strings.

*Actions:*

- **PsyNetSkills:** Add a setup verification check or troubleshooting note that `xgettext --version` should pass before starting cross-cultural challenge attempts that require translation readiness. Confidence: high. Impact: medium. Status: considering.
