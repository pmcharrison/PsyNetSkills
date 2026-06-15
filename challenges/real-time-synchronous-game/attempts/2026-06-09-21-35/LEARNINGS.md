# Learnings

## Realtime websocket messages in debug mode

Dallinger queues ordinary websocket payloads for worker processing. In local
debug evidence runs without a separate worker, the live game stayed on
"Connecting..." until participant messages were sent with `immediate: true` and
the server resolved the participant from the payload.

*Actions:*
- **PsyNetSkills:** Add a note to realtime challenge guidance explaining when websocket evidence runners should use immediate messages or start workers. Confidence: medium. Impact: medium. Status: considering.
## Signal-probability defaults differ between public instructions and criteria

The public challenge instructions specify low/high Bernoulli defaults of
0.33/0.67, while the copied evaluation criteria mention 0.25/0.75. This attempt
implemented the public instructions.

*Actions:*
- **PsyNetSkills:** Reconcile the real-time synchronous game challenge instructions and criteria so future attempts target one default probability pair. Confidence: high. Impact: medium. Status: considering.
