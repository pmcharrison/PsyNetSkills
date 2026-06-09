# Learnings

## Handler-only WebSocket elements need no-op timeline consumption

Custom `WebSocketElt` subclasses used only for message handling still appear in
the participant timeline. Overriding `consume` and `render` as no-ops prevents
bot/test participants from hitting the abstract base `Elt.consume`.

*Actions:*
- **PsyNetSkills:** Add this gotcha to experiment implementation guidance for custom realtime channels. Confidence: medium. Status: considering.

## Bot fallback scoring requires saved round-page answers

When browser WebSockets perform live scoring, automated bot tests still need a
non-WebSocket scoring path. The round page must persist bot answers before a
post-round `GroupBarrier` can reconstruct proposals and decisions.

*Actions:*
- **PsyNetSkills:** Document the paired pattern of WebSocket live scoring plus barrier-backed bot fallback scoring for synchronous game challenges. Confidence: high. Status: considering.
