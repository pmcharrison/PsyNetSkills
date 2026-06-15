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

## Neutral UI chrome and analysis figures need explicit review artifacts

The evaluator noted that the top progress bar stayed blue despite neutral button
styling, and that the requested matrix figure was available in the notebook but
not embedded as a standalone PNG in the attempt summary.

*Actions:*
- **PsyNetSkills:** Add concise psychophysics guidance requiring final visual
  verification of PsyNet progress-bar selectors and standalone PNG embedding for
  requested analysis figures. Confidence: high. Impact: medium. Status:
  completed. Notes: Added to `.cursor/skills/psychophysics/SKILL.md`.
