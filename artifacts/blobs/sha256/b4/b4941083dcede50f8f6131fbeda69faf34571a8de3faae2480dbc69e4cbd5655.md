# Adaptive real-time Prisoner's Dilemma

This PsyNet experiment implements a dyadic 10-round Prisoner's Dilemma with
synchronous grouping, barriers, chat/no-chat treatments, a dedicated game
websocket state channel, and active-inference treatment assignment.

The global `EXPERIMENT_MODE` in `experiment.py` can be set to `adaptive` or
`static`. Locally, this can be overridden with `PD_EXPERIMENT_MODE=static`.

Run from this directory:

- `python experiment.py`
- `psynet test local`
- `python simulate_procedure.py`
