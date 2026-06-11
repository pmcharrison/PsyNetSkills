# Learnings

## Separate behavioral flow from PsyNet architecture

A challenge can require PsyNet TrialMaker/Node architecture without requiring every game round to be a separate PsyNet page sequence. The corrected design keeps one WebSocket-driven live game as the behavioral flow, then embeds that flow as a `ChainTrial` with a `ChainNode` summary and `ChainTrialMaker` dyad synchronization.

*Actions:*
- **PsyNetSkills:** Consider documenting this pattern for synchronous WebSocket tasks: use PsyNet TrialMaker/Node constructs for allocation and persistence while allowing the browser to manage rapid within-trial live interaction over WebSockets. Confidence: high. Status: considering.

## Preserve explicit interface requirements during architectural corrections

The corrected attempt restored the WebSocket flow and PsyNet TrialMaker/Node
architecture, but the evaluator noted that it dropped the required three.js
interface. Future correction attempts should re-check every public interface
requirement after structural refactors, especially when copying or simplifying a
previous implementation.

*Actions:*
- **PsyNetSkills:** Consider adding a correction-pass checklist item to verify that UI/media requirements from the public instructions are still satisfied after architectural rewrites. Confidence: high. Status: considering.
