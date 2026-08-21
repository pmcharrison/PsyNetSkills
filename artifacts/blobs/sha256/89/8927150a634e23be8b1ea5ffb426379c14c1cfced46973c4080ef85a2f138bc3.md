# Repeated Ultimatum Game

This PsyNet experiment pairs two participants with `SimpleGrouper`, runs one
unscored timeout demonstration round, then runs 10 scored Ultimatum Game rounds.

Each round randomly assigns proposer and responder roles. The proposer chooses a
0-10 coin offer; the responder accepts or rejects after receiving a live
WebSocket update. Accepted offers split the 10-coin endowment, rejected offers
award 0 to both players, and timed-out decisions skip the round without changing
scores.

Run from this directory with:

```bash
uv pip install -r constraints.txt
psynet test local
psynet debug local
```
