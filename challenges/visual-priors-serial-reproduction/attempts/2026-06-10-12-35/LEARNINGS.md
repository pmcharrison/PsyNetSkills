# Learnings

## Bot responses on custom `Page` classes

PsyNet bots submit the value returned by `get_bot_response` as the formatted
answer. For custom `Page` classes, the bot path can bypass `format_answer` unless
`get_bot_response` explicitly returns the same structured answer that a browser
response would produce.

*Actions:*
- **PsyNetSkills:** Add a note to experiment implementation guidance about
  matching bot responses to formatted custom-page answers. Confidence: medium.
  Status: considering.

## Local export credential workaround

`psynet export local --username ... --password ...` still attempted to read
`dashboard_password` from config in this environment. A temporary, restored
`config.txt` credential insertion was needed to export `data.zip`.

*Actions:*
- **PsyNet:** Check whether `psynet export local` should honor the CLI password
  option before falling back to config. Confidence: medium. Status: considering.
