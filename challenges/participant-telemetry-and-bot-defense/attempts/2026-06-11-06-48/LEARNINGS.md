# Learnings

## Make helper-script imports explicit in attempt tests

Running a targeted pytest node from a nested PsyNet experiment directory did not
automatically expose sibling helper scripts on `sys.path`, even when the shell
was already in that directory. Adding the experiment directory explicitly in
`test.py` made the scoring-unit test and PsyNet test collection use the same
imports.

*Actions:*
- **PsyNetSkills:** Consider adding a short note to attempt or experiment
  implementation guidance about explicit import paths for nested attempt helper
  scripts. Confidence: medium. Status: considering.
