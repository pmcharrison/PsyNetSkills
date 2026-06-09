# Learnings

## Use PsyNet events for timed auto-submit behavior

Inline browser timers were not reliable enough for timeout-to-default behavior in
the first participant recording. Moving the default response into a PsyNet
`Event` tied to `trialStart` made the timeout visible and repeatable.

*Actions:*
- **PsyNetSkills:** Add a short timeout auto-submit pattern to experiment challenge guidance. Confidence: medium. Status: considering.
