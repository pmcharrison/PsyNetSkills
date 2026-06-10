# Learnings

## Broadcast websocket payloads are not private

Dallinger channel broadcasts are useful for public synchronization, but target-filtered payloads still traverse every subscribed browser. Private per-participant signals should be fetched through an authenticated participant route or another truly private transport.

*Actions:*

- **PsyNetSkills:** Add a realtime challenge note warning that websocket broadcasts must not carry private payloads, even when clients filter by recipient id. Confidence: high. Status: considering.
