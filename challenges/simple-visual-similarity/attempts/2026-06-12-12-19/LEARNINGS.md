# Learnings

## Prefer flattened PsyNet export columns for repeated objects

PsyNet simulated exports can serialize repeated nested objects with JSON reference markers such as `py/id`, while the same table may also provide flattened columns for trial-level fields. The analysis script initially read only the nested `definition` JSON and failed on self-pairs until it preferred the flattened `stimulus_a` and `stimulus_b` columns.

*Actions:*

- **PsyNetSkills:** Update experiment-analysis guidance to recommend preferring flattened export columns over nested JSON definitions when both are present in PsyNet CSV exports. Confidence: high. Impact: medium. Status: considering.
