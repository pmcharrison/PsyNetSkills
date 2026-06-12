---
title: Adaptive memory testing experiment
type: experiment implementation
difficulty: 9
authors: [lucasgautheron]
---

Implement a PsyNet experiment that estimates each participant's memory ability
efficiently by adaptively selecting number-string recall trials.

Participants should complete 10 trials. On each trial, the experiment presents a
string of digits, then asks the participant to reproduce the string from memory.
The participant's response should be scored as correct only when it exactly
matches the target string.

The experiment should:

- Generate digit strings whose length can vary from trial to trial.
- Adaptively choose the length of each new string to maximize the expected
  information gain about the participant's ability.
- Make the adaptive mode easy to disable. When adaptive mode is disabled, choose
  each sequence length randomly between 2 and 20 inclusive.
- Use variational inference to approximate the posterior distribution used by
  the adaptive policy.
- Cache the previous posterior state and use it to initialize subsequent
  posterior fits, so that trial-by-trial updates are more efficient.
- Save enough trial metadata to reconstruct the target string, response,
  correctness, selected length, posterior state, and acquisition value used for
  each trial.
- Include a simulation, analysis script, or notebook that demonstrates the
  adaptive policy learning from synthetic participants with different abilities.

Use the following hierarchical response model, using the shape-rate
parameterization for Gamma distributions:

```text
l_0 = 8
mu ~ Gamma(2, 2)
alpha ~ Gamma(2, 1)
r_i ~ Gamma(alpha, alpha / mu), i = 1, ..., N
p_ij = exp(-r_i * l_j / l_0)
y_ij ~ Bernoulli(p_ij)
```

Here `y_ij` is whether participant `i` recalled number string `j` correctly,
`l_j` is the length of the presented string, `r_i` is the
participant-specific memory decay rate, `mu` is the population mean decay rate,
`alpha` controls between-participant variation, and `l_0 = 8` is a fixed
scaling factor. Lower values of `r_i` correspond to better memory performance.

The adaptive procedure should consider plausible candidate lengths before each
trial and select the candidate with maximal expected information gain under the
current variational posterior. The implementation should document how candidate
lengths are bounded and how the posterior cache is represented.
