# Initial simulation analysis

- Run ID: `initial`
- Revision: `initial`
- Participants: 12
- Trials: 96

## Profile-by-condition summary

| Profile | Condition | N | Accuracy | Target | Semantic lure | Recent lure | Neutral lure | Median RT ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| mock_llm_memory_limited | interference | 12 | 0.167 | 2 | 0 | 10 | 0 | 2105 |
| mock_llm_memory_limited | literal | 12 | 0.750 | 9 | 3 | 0 | 0 | 2105 |
| psynet_bot_rule | interference | 12 | 1.000 | 12 | 0 | 0 | 0 | 1205 |
| psynet_bot_rule | literal | 12 | 1.000 | 12 | 0 | 0 | 0 | 1205 |
| scripted_noisy | interference | 12 | 0.667 | 8 | 2 | 0 | 2 | 2956 |
| scripted_noisy | literal | 12 | 0.667 | 8 | 2 | 1 | 1 | 2956 |
| semantic_bias | interference | 12 | 0.167 | 2 | 10 | 0 | 0 | 1749 |
| semantic_bias | literal | 12 | 0.167 | 2 | 10 | 0 | 0 | 1749 |

## Expectation comparison

- `psynet_bot_rule`: expected near ceiling in both conditions.
- `scripted_noisy`: expected lower accuracy with weak condition specificity and slower responses.
- `mock_llm_memory_limited`: expected literal success but recent-lure vulnerability on interference trials.
- `semantic_bias`: expected semantic-lure errors, especially on interference trials.

## Flags

- No preregistered expectation flags were triggered.
