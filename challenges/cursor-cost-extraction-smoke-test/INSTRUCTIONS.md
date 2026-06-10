---
title: Cursor cost extraction smoke test
type: workflow validation
difficulty: 1
authors: [pmcharrison]
---

# Cursor cost extraction smoke test

This stub challenge exists to validate the Cursor cost import workflow. It does
not ask the agent to implement a PsyNet experiment. Instead, it provides a small
dashboard-visible challenge where a deliberately minimal attempt can record
Cursor Cloud metadata and confirm that cost import resolves by exact Cloud Agent
ID.

The expected implementation is a short note explaining that no participant-facing
experiment is required. The useful evidence is the attempt metadata in
`agent.json`, especially `cursor_conversation_id` and `run_cost`.
