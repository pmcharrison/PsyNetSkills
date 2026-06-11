# Revised simulation analysis

- Run ID: `revised`
- Revision: `revised`
- Participants: 12
- Trials: 96

## Profile-by-condition summary

| Profile | Condition | N | Accuracy | Target | Semantic lure | Recent lure | Neutral lure | Median RT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| mock_llm_memory_limited | interference | 12 | 0.750 | 9 | 0 | 3 | 0 | 2082 |
| mock_llm_memory_limited | literal | 12 | 1.000 | 12 | 0 | 0 | 0 | 2082 |
| psynet_bot_rule | interference | 12 | 1.000 | 12 | 0 | 0 | 0 | 1226 |
| psynet_bot_rule | literal | 12 | 1.000 | 12 | 0 | 0 | 0 | 1226 |
| scripted_noisy | interference | 12 | 0.917 | 11 | 1 | 0 | 0 | 2906 |
| scripted_noisy | literal | 12 | 0.750 | 9 | 1 | 2 | 0 | 2906 |
| semantic_bias | interference | 12 | 0.333 | 4 | 8 | 0 | 0 | 1770 |
| semantic_bias | literal | 12 | 0.417 | 5 | 7 | 0 | 0 | 1770 |

## Expectation comparison

- `psynet_bot_rule`: expected near ceiling in both conditions.
- `scripted_noisy`: expected lower accuracy with weak condition specificity and slower responses.
- `mock_llm_memory_limited`: expected literal success but recent-lure vulnerability on interference trials.
- `semantic_bias`: expected semantic-lure errors, especially on interference trials.

## Flags

- No preregistered expectation flags were triggered.
