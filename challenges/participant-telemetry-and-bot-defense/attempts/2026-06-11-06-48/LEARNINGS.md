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
  scripts. Confidence: medium. Impact: low. Status: considering.
## Preserve PsyNet generated-asset ignores in nested attempts

`psynet test local` creates `source_code.zip` and may create `static/assets`.
When building a nested attempt experiment from scratch rather than copying a full
demo template, omitting these ignore rules can make the PsyNet launch guard fail
before the experiment starts.

*Actions:*
- **PsyNetSkills:** Consider expanding the attempt-challenge reminder about
  copying standard support files to name `source_code.zip` and `static/assets`
  ignore rules explicitly. Confidence: high. Impact: low. Status: considering.
## Use richer ambiguity in telemetry challenge simulations

The evaluation noted that future telemetry attempts would be stronger if the
task and simulated profiles created more realistic ambiguity, for example a
richer real experimental task or subtler LLM-style response profiles rather than
only obvious fast, uniform, or failed-check profiles.

*Actions:*
- **PsyNetSkills:** Consider updating this challenge's public examples or future
  attempt guidance to encourage nuanced simulated profiles that test review
  rules under ambiguous but still local and ethical conditions. Confidence:
  medium. Impact: medium. Status: considering.
