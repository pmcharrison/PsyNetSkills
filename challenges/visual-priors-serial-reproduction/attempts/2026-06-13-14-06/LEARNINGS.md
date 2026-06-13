# Learnings

## Plan gate for experiment attempts

Experiment implementation challenges require a committed `PLAN.md` and human review before coding, even when the user asks the agent to retry an attempt.

*Actions:*

- **PsyNetSkills:** Consider adding a short `/attempt-challenge` response template for experiment implementation retries that explains the plan-review pause and the expected next user action. Confidence: medium. Impact: low. Status: considering.

## Unique session IDs for repeated custom pages

Consecutive custom `Page` instances with the default `session_id` can preserve the browser session and update the DOM without rerunning page scripts. Repeated interactive pages should use distinct session IDs or handle PsyNet's `pageUpdated` event explicitly.

*Actions:*

- **PsyNetSkills:** Add a note to the front-end experiment development skill that repeated custom `Page` classes with JavaScript event handlers need unique `session_id` values or `pageUpdated` handling. Confidence: high. Impact: medium. Status: considering.
