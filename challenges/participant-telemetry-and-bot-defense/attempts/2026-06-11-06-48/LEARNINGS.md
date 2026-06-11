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

## Preserve PsyNet generated-asset ignores in nested attempts

`psynet test local` creates `source_code.zip` and may create `static/assets`.
When building a nested attempt experiment from scratch rather than copying a full
demo template, omitting these ignore rules can make the PsyNet launch guard fail
before the experiment starts.

*Actions:*
- **PsyNetSkills:** Consider expanding the attempt-challenge reminder about
  copying standard support files to name `source_code.zip` and `static/assets`
  ignore rules explicitly. Confidence: high. Status: considering.
