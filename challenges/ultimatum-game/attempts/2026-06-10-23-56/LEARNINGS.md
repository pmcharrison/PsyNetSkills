# Learnings

## Separate behavioral flow from PsyNet architecture

A challenge can require PsyNet TrialMaker/Node architecture without requiring every game round to be a separate PsyNet page sequence. The corrected design keeps one WebSocket-driven live game as the behavioral flow, then embeds that flow as a `ChainTrial` with a `ChainNode` summary and `ChainTrialMaker` dyad synchronization.

*Actions:*
- **PsyNetSkills:** Consider documenting this pattern for synchronous WebSocket tasks: use PsyNet TrialMaker/Node constructs for allocation and persistence while allowing the browser to manage rapid within-trial live interaction over WebSockets. Confidence: high. Status: considering.
