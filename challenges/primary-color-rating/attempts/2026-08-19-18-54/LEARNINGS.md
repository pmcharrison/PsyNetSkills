# Learnings

## Local PsyNet master still lacks the audit CLI

`git fetch origin master` succeeded, but `origin/master` has no `psynet/audit`
package and no `psynet audit` command. Checking it out would have dropped the
CLI this dogfood needed. The attempt stayed on the local audit feature branch
and recorded that in `agent.json`.

*Actions:*

- **PsyNetSkills:** Keep attempt-challenge refresh guidance aligned with AGENTS.md: use a PsyNet revision that includes `psynet audit` rather than resetting to master when that would drop the CLI. Confidence: high. Impact: high. Status: considering.
- **PsyNet:** Merge the audit CLI to PsyNet master so challenge attempts can refresh with `git checkout master && git pull --ff-only origin master`. Confidence: high. Impact: high. Status: considering.

## Port 5000 was already held by another local debug session

The first `psynet test local` timed out because gunicorn could not bind
`0.0.0.0:5000`. A leftover `psynet debug local` from
`~/psynet-experiments/dogfood_setup_audit` was still listening. Stopping that
specific PID unblocked the test.

*Actions:*

- **PsyNetSkills:** Before `psynet test local` in Cursor Cloud, check that port 5000 is free and stop any leftover debug PID rather than assuming a clean machine. Confidence: high. Impact: medium. Status: considering.

## RatingControl answers are stored as dicts on StaticTrial

`RatingControl.format_answer` unwraps to a scalar in some paths, but
`ColorRatingTrial.answer` in the bot check and CSV export was `{"rating": n}`.
Asserting `trial.answer in {1, ..., 7}` raised `TypeError: unhashable type: 'dict'`.
The export also provides a `rating` column.

*Actions:*

- **PsyNet:** Document that `StaticTrial.answer` for `RatingControl` may remain `{"rating": n}` even though `RatingControl.format_answer` unwraps to a scalar. Confidence: high. Impact: medium. Status: considering.
- **PsyNetSkills:** In experiment-implementation guidance, tell agents to inspect a bot `trial.answer` (or the trial CSV) before writing `test_check_bot` equality checks for rating pages. Confidence: medium. Impact: medium. Status: considering.

## Repo gitignore hid audit-layout logs

`*.log` is ignored except `challenges/*/attempts/*/evidence/*.log`. New attempts
write logs under `logs/`, so test logs would not have been committed without a
new exception.

*Actions:*

- **PsyNetSkills:** Keep a gitignore exception for `challenges/*/attempts/*/logs/*.log` now that attempts use the audit packet layout. Confidence: high. Impact: medium. Status: completed. Notes: Added in this dogfood attempt.

## EVALUATION.md template checklist did not pass validation

The attempt template used `- [ ]` with no trailing space. `psynetsk-validate`
requires `- [ ] ` (space after the brackets) once `ended_at` is set and
`CRITERIA.md` exists, so a completed attempt failed until the checkbox line
was given text.

*Actions:*

- **PsyNetSkills:** Make the attempt EVALUATION.md template checkbox a valid `- [ ] …` line so completed attempts pass validation before human scoring. Confidence: high. Impact: medium. Status: completed. Notes: Updated the attempt template in this dogfood run.
