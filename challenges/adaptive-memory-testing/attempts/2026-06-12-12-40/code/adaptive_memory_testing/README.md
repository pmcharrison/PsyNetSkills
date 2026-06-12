# Adaptive memory testing

This PsyNet experiment administers 10 digit-string recall trials. Sequence
lengths are bounded to integers from 2 through 20 inclusive.

Adaptive mode is enabled by default. Disable it for random-length trials with:

```bash
ADAPTIVE_MEMORY_ADAPTIVE=0 psynet test local
```

The adaptive policy uses a NumPy mean-field variational approximation to the
specified hierarchical response model. The cached posterior is stored as a
JSON-serializable dictionary with the variable order, posterior mean vector,
posterior standard deviation vector, ELBO, observation count, and iteration
count. Each trial stores `posterior_state_before`, `posterior_state_after`,
`selected_length`, `target_string`, response, score, and acquisition metadata.

Run the standalone synthetic-participant demonstration with:

```bash
python simulate_policy.py --output-dir simulation_output
```
