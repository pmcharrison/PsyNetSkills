# Learnings

## Prefer native PsyNet Graphics for visual-memory tasks

The evaluator found the custom JavaScript canvas implementation clunky and
jittery, and requested a more idiomatic PsyNet implementation that stays closer
to existing PsyNet demos. For visual reproduction tasks, native PsyNet Graphics
objects should be the default approach unless the required interaction cannot be
expressed with the framework.

*Actions:*
- **PsyNetSkills:** Update experiment implementation guidance to emphasize
  native PsyNet Graphics for dot, shape, and click-coordinate tasks before
  introducing custom JavaScript. Confidence: high. Impact: high. Status: considering.
## Bot responses on custom `Page` classes

PsyNet bots submit the value returned by `get_bot_response` as the formatted
answer. For custom `Page` classes, the bot path can bypass `format_answer` unless
`get_bot_response` explicitly returns the same structured answer that a browser
response would produce.

*Actions:*
- **PsyNetSkills:** Add a note to experiment implementation guidance about
  matching bot responses to formatted custom-page answers. Confidence: medium. Impact: low. Status: considering.
## Local export credential workaround

`psynet export local --username ... --password ...` still attempted to read
`dashboard_password` from config in this environment. A temporary, restored
`config.txt` credential insertion was needed to export `data.zip`.

*Actions:*
- **PsyNet:** Check whether `psynet export local` should honor the CLI password
  option before falling back to config. Confidence: medium. Impact: low. Status: completed.
  Notes: Fixed upstream in https://gitlab.com/PsyNetDev/PsyNet/-/merge_requests/1081.
