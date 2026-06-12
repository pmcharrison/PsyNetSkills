# Adaptive memory testing

This PsyNet experiment administers 10 digit-string recall trials. Each trial stores the target string, participant response, exact-match correctness, selected length, posterior cache, and acquisition diagnostics in the trial definition.

## Adaptive mode

Adaptive mode is enabled by default. Disable it with:

```bash
ADAPTIVE_MEMORY_ADAPTIVE=0 psynet test local
```

When disabled, each trial samples a sequence length uniformly from 2 through 20 inclusive.

## Posterior cache

`participant.var.memory_posterior_state` stores a JSON-serializable diagonal Gaussian variational posterior over unconstrained `log_mu`, `log_alpha`, and `log_r`. It contains means, log standard deviations, ELBO diagnostics, optimizer status, the number of observations, and derived ability summaries. The previous cache initializes the next posterior fit.

## Simulation

Run:

```bash
python simulate_policy.py --output-dir ../../evidence/analyses
```

The script simulates low-, medium-, and high-ability participants and writes CSV/JSON evidence showing selected lengths and posterior ability estimates over trials.
