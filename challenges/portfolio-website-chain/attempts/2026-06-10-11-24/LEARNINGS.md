# Learnings

## Custom experiment settings should not be added directly to `config.txt`

Dallinger rejects unregistered keys in `config.txt` before the experiment module
can load. OpenRouter settings for this attempt therefore work through
environment variables, with code-level defaults and optional registered config
lookups.

*Actions:*
- **PsyNetSkills:** Clarify in experiment implementation guidance that arbitrary custom settings should not be written to `config.txt` unless the deployment registers them first. Confidence: medium. Status: considering.

## Radio button bot answers need a subclass in current PsyNet

`TextControl` accepts `bot_response`, but `RadioButtonControl` does not expose
that constructor argument in the current PsyNet checkout. A small subclass with
`get_bot_response` keeps later-node bot flows deterministic.

*Actions:*
- **PsyNetSkills:** Add a reminder to challenge guidance to exercise later-node page construction, not only direct transition helpers. Confidence: high. Status: considering.
- **PsyNet:** Consider aligning `RadioButtonControl` with other option controls by accepting a bot response argument in its constructor. Confidence: low. Status: considering.
