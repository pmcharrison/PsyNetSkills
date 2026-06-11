# Learnings

## Handler-only WebSocket elements need no-op timeline consumption

Custom `WebSocketElt` subclasses used only for message handling still appear in
the participant timeline. Overriding `consume` and `render` as no-ops prevents
bot/test participants from hitting the abstract base `Elt.consume`.

*Actions:*
- **PsyNetSkills:** Add guidance that handler-only custom `WebSocketElt` subclasses for realtime channels should implement no-op `consume` and `render` methods so bots and tests do not hit abstract base methods. Confidence: medium. Status: considering.

## Bot fallback scoring requires saved round-page answers

When browser WebSockets perform live scoring, automated bot tests still need a
non-WebSocket scoring path. The round page must persist bot answers before a
post-round `GroupBarrier` can reconstruct proposals and decisions.

*Actions:*
- **PsyNetSkills:** Document the paired pattern of WebSocket live scoring plus barrier-backed bot fallback scoring for synchronous game challenges. Confidence: high. Status: considering.

## Synchronous game evidence should cover every timeout role and reward mapping

The evaluation identified that this attempt demonstrated proposer timeout but
not responder timeout, and did not verify that monetary rewards correspond to
accumulated scores. Future synchronous economic-game attempts should explicitly
exercise each timed decision role and include a check tying final payment logic
to accumulated score.

*Actions:*
- **PsyNetSkills:** Expand experiment evidence guidance for synchronous economic games to require role-specific timeout coverage and reward-to-score validation. Confidence: high. Status: considering.
