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
- Use variational inference to approximate the posterior distribution used by
  the adaptive policy.
- Cache the previous posterior state and use it to initialize subsequent
  posterior fits, so that trial-by-trial updates are more efficient.
- Save enough trial metadata to reconstruct the target string, response,
  correctness, selected length, posterior state, and acquisition value used for
  each trial.
- Include a simulation, analysis script, or notebook that demonstrates the
  adaptive policy learning from synthetic participants with different abilities.

Use the following hierarchical response model:

```text
y ~ Bernoulli(p)
p = exp(-exp(theta_i) * l / l_0)
theta_i ~ Normal(mu, sigma)
sigma ~ Exponential(1)
mu ~ Normal(0, 1)
```

Here `y` is whether the participant recalled the number string correctly, `l` is
the length of the presented string, `theta_i` is the participant-specific memory
ability parameter, and `l_0 = 8` is a fixed scaling factor.

The adaptive procedure should consider plausible candidate lengths before each
trial and select the candidate with maximal expected information gain under the
current variational posterior. The implementation should document how candidate
lengths are bounded and how the posterior cache is represented.
