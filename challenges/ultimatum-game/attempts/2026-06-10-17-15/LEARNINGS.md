# Learnings

## Use `python3` in minimal Cursor Cloud shells

The shell does not expose `python`, so setup scripts that assume it can fail before creating attempt metadata.

*Actions:*
- **PsyNetSkills:** Consider changing attempt setup examples to call `python3` or `uv run python` explicitly. Confidence: medium. Status: considering.

## Browser evidence needs action paths independent from WebSocket readiness

The live UI rendered and grouped participants, but manual testing showed action clicks could be lost when they depended solely on a ready WebSocket. Posting authenticated actions to a normal experiment route while keeping WebSockets for broadcasts made the participant path reliable.

*Actions:*
- **PsyNetSkills:** Consider adding this HTTP-action-plus-WebSocket-broadcast pattern to synchronous challenge guidance. Confidence: medium. Status: considering.

## Vendored ES modules may require sibling build files

The latest Three.js module imports `three.core.min.js`; vendoring only `three.module.min.js` caused browser-only failures that automated bot tests could not catch.

*Actions:*
- **PsyNetSkills:** For challenges requiring vendored browser libraries, document checking browser network logs for secondary module imports. Confidence: high. Status: considering.
