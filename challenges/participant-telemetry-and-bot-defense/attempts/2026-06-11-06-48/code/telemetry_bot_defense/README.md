# Local participant telemetry demo

This PsyNet experiment presents six brief statement-rating trials, including one
attention check and related items for coarse response-consistency review.

Run from this directory:

- `python experiment.py`
- `python simulate_profiles.py`
- `python score_telemetry.py`
- `psynet test local`

The simulated export and scoring outputs are written under the attempt
`evidence/` directory. All profiles are local mock data only. Review flags are
manual-review prompts and are not claims that a participant is a bot, AI system,
or LLM-assisted.
