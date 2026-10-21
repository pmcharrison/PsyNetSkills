# Implementation reference

Use the real-time websocket architecture from the adaptive real-time Prisoner's
Dilemma attempt as the implementation pattern:

- Repository path:
  `challenges/adaptive-realtime-prisoners-dilemma/attempts/2026-06-30-14-24/code/adaptive_realtime_prisoners_dilemma/experiment.py`
- Public URL:
  <https://github.com/pmcharrison/PsyNetSkills/blob/main/challenges/adaptive-realtime-prisoners-dilemma/attempts/2026-06-30-14-24/code/adaptive_realtime_prisoners_dilemma/experiment.py>

The relevant pattern is the generic `LiveEvent`, `LiveSession`, and
`LiveSessionWebSocket` design for persisted live events, live session state, and
websocket broadcasts. The adaptive treatment-assignment logic in that attempt is
not part of this challenge.
