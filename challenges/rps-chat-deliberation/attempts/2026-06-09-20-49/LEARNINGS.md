# Learnings

## Minimal PsyNet experiment scaffold completeness

PsyNet local launch checks require standard experiment support files such as
`.gitignore`, even for a compact challenge attempt that only copies the visible
Python/config/test files from a demo.

*Actions:*
- **PsyNetSkills:** Update challenge attempt scaffolding guidance to include the standard PsyNet experiment `.gitignore` when copying a minimal demo into `code/`. Confidence: high. Status: considering.

## Multi-participant evidence needs isolated browser profiles

Opening multiple PsyNet participants in one Chrome profile can collide through
shared browser/session state and cause misleading early-end behavior during
grouping. Separate `--user-data-dir` profiles paired correctly.

*Actions:*
- **PsyNetSkills:** Add a note to participant evidence guidance recommending separate browser profiles or Playwright contexts for multi-participant recordings. Confidence: high. Status: considering.

## Check native timed-page patterns before custom JavaScript

The evaluator liked the concise `psynet.nextPage` transition but noted that
PsyNet may already provide a built-in way to implement timed pages through page
or trial parameters. Future attempts should check for that option before adding
even small custom JavaScript.

*Actions:*
- **PsyNetSkills:** Add a reminder to experiment implementation guidance to look for native timed-page or auto-advance APIs before using custom JavaScript for page timing. Confidence: medium. Status: considering.
