# Participant telemetry review report

This local demonstration implements a brief PsyNet statement-rating task with one embedded attention check and related-item consistency opportunities. The telemetry fields include participant and trial identifiers, item metadata, responses, attention-check correctness, client trial start and submit times when available, response latency, local profile labels, and server receipt time.

Simulated PsyNet-shaped data are generated locally by `simulate_profiles.py`; no real participant data, recruitment service, AWS, Prolific, Cint, or production credential is used.

The review script applies transparent rules: fast median latency, failed attention check, missing timing telemetry, low response variance, and coarse response-consistency mismatches after reverse-coding negative paired items.

Flags are conservative manual-review prompts only. They do not prove that a respondent is a bot, an AI system, or LLM-assisted, and they should not be used for automatic rejection.

## Review decisions

| Participant | Profile | Decision | Signals |
| --- | --- | --- | --- |
| P001 | mock_human_like | no_review_flag | none |
| P002 | mock_fast_uniform | manual_review | fast_median_latency:217ms;attention_check_failed;low_response_variance |
| P003 | mock_attention_fail | manual_review | attention_check_failed |
| P004 | mock_inconsistent_pair | manual_review | response_consistency_mismatch:focus_environment;response_consistency_mismatch:planning |
| P005 | mock_missing_telemetry | manual_review | missing_timing_telemetry |

## Flagged profiles

- `P002` (`mock_fast_uniform`): fast_median_latency:217ms;attention_check_failed;low_response_variance.
- `P003` (`mock_attention_fail`): attention_check_failed.
- `P004` (`mock_inconsistent_pair`): response_consistency_mismatch:focus_environment;response_consistency_mismatch:planning.
- `P005` (`mock_missing_telemetry`): missing_timing_telemetry.

## Limits

- Fast responses can reflect interface familiarity, accidental clicks, or other benign causes.
- Failed checks can indicate misunderstanding, distraction, or ambiguous instructions.
- Consistency mismatches can reflect genuine opinion nuance, not deception.
- Missing telemetry can result from browser, network, or instrumentation issues.
