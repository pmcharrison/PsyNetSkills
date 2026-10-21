# Initial vs revised comparison

| Profile | Condition | Initial accuracy | Revised accuracy | Delta | Initial recent lures | Revised recent lures | Initial semantic lures | Revised semantic lures |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| mock_llm_memory_limited | interference | 0.167 | 0.750 | 0.583 | 10 | 3 | 0 | 0 |
| mock_llm_memory_limited | literal | 0.750 | 1.000 | 0.250 | 0 | 0 | 3 | 0 |
| psynet_bot_rule | interference | 1.000 | 1.000 | 0.000 | 0 | 0 | 0 | 0 |
| psynet_bot_rule | literal | 1.000 | 1.000 | 0.000 | 0 | 0 | 0 | 0 |
| scripted_noisy | interference | 0.667 | 0.917 | 0.250 | 0 | 0 | 2 | 1 |
| scripted_noisy | literal | 0.667 | 0.750 | 0.083 | 1 | 2 | 2 | 1 |
| semantic_bias | interference | 0.167 | 0.333 | 0.166 | 0 | 0 | 10 | 8 |
| semantic_bias | literal | 0.167 | 0.417 | 0.250 | 0 | 0 | 10 | 7 |
