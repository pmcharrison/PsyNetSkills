# Learnings

## Use `python3` in minimal Cursor Cloud shells

The shell does not expose `python`, so setup scripts that assume it can fail before creating attempt metadata.

*Actions:*
- **PsyNetSkills:** Consider changing attempt setup examples to call `python3` or `uv run python` explicitly. Confidence: medium. Status: considering.
