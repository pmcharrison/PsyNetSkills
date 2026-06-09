# Learnings

## Use PsyNet events for timed auto-submit behavior

Inline browser timers were not reliable enough for timeout-to-default behavior in
the first participant recording. Moving the default response into a PsyNet
`Event` tied to `trialStart` made the timeout visible and repeatable.

*Actions:*
- **PsyNetSkills:** Add a short timeout auto-submit pattern to experiment challenge guidance. Confidence: medium. Status: considering.

## Validate payoff mapping against final experiment state

The evaluator noted that the attempt did not check whether participant bonuses
correspond to final coin balances. Future economic-game attempts should include
an explicit assertion or evidence note connecting the final task state to the
payment/bonus calculation.

*Actions:*
- **PsyNetSkills:** Add a payoff-validation reminder to experiment evidence guidance for economic-game challenges. Confidence: medium. Status: considering.
