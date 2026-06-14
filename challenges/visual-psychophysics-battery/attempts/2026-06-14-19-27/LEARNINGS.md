# Learnings

## Browser validation catches PsyNet graphics timing issues

Bot tests passed before the discrimination response controls were usable in a
real browser. Playwright evidence showed that response buttons could remain
disabled when response enabling depended on an empty graphics frame or a joined
response page. A page-level event bridge that registered PsyNet's standard
`responseEnable` and `submitEnable` events after the timed blank resolved the
browser path while preserving event-log reaction times.

*Actions:*
- **PsyNetSkills:** Update psychophysics or experiment-validation guidance to
  recommend browser-driven checks for timed `GraphicPrompt` response activation,
  especially when controls activate after blank frames. Confidence: high. Impact:
  medium. Status: considering.
- **PsyNet:** Consider documenting the most reliable pattern for delayed
  response activation after timed graphics frames, including whether empty frames
  should trigger `activate_control_response`. Confidence: medium. Impact: medium.
  Status: considering.
