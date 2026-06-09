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
