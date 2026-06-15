# Plan

## Methods

Participants will complete a 10-trial digit-span recall task. Each trial will
show a digit string, briefly ask the participant to memorize it, and then request
an exact transcription. The target stimulus will be a uniformly sampled string
of decimal digits at the selected length. Responses will be scored as correct
only when the submitted text exactly matches the target string.

The independent variable controlled by the adaptive policy is sequence length.
Candidate lengths will be the bounded integer range 2 through 20 inclusive, as
specified by the public challenge. The adaptive procedure will choose one
candidate per trial. When adaptive mode is disabled, each trial will sample a
length uniformly from the same range, keeping the participant workflow and
metadata format unchanged.

The response model will follow the challenge specification:

- `mu ~ Gamma(2, 2)`
- `alpha ~ Gamma(2, 1)`
- `r_i ~ Gamma(alpha, alpha / mu)`
- `p_ij = exp(-l_j / (l_0 * r_i))`
- `y_ij ~ Bernoulli(p_ij)`

The fixed scale will be `l_0 = 8`. The experiment will estimate the positive
participant-specific memory ability `r_i` online from the participant's own
previous trials while retaining the hierarchical hyperpriors in the model.

## Implementation

The attempt will implement a self-contained PsyNet experiment under
`code/adaptive_memory_testing/`. The experiment will use a within-participant
chain-style trial maker so that each new trial definition can be generated from
the participant's previous recall outcomes. This avoids pre-materializing every
possible node and keeps the adaptive selection local to the participant.

The core classes will be:

- `DigitRecallTrial`, a PsyNet trial class whose definition contains
  `target_string`, `length`, `adaptive_mode`, `acquisition_value`,
  `posterior_state_before`, and policy diagnostics.
- `AdaptiveDigitRecallTrialMaker`, a trial maker that creates one within-chain
  sequence per participant and generates exactly 10 recall trials.
- `AdaptivePolicy`, a pure-Python helper responsible for fitting the posterior,
  caching state, simulating candidate outcomes, and choosing the next length.

The participant timeline will contain an instruction page followed by the recall
trial maker. Each trial will contain an encoding page with the target string and
a response page with a text input restricted to digits. Bots will receive a
mixture of synthetic abilities so that automated tests and simulations exercise
both high- and low-accuracy participants.

## Variational inference and cache representation

The adaptive policy will use lightweight NumPy mean-field variational inference
to approximate the posterior over unconstrained `log_mu`, `log_alpha`, and
`log_r_i` given the participant's observed `(length, correct)` history. The
posterior cache will be represented as JSON-serializable metadata containing:

- the previous posterior mean vector;
- the previous posterior standard deviation vector;
- the variable order used to interpret those vectors;
- transformed posterior means for `mu`, `alpha`, and `r_i`;
- the number of observations used for the fit;
- fitting diagnostics such as ELBO loss and draw count.

On the first trial, the cache will be absent and the policy will use the prior.
On subsequent trials, the previous cache will initialize the next variational
fit so that only the incremental participant history needs to refine the
posterior. The cached state before and after each trial will be saved in trial
metadata, making the adaptive path reconstructable from exported data.

## Acquisition function

For each candidate length from 2 to 20 inclusive, the policy will estimate the
predictive probability of a correct response under the current variational
posterior. It will then evaluate the two possible outcomes for that candidate
and approximate expected information gain as the expected reduction in posterior
entropy after observing that outcome:

`EIG(l) = H(q_current(r_i)) - E_y[H(q_next(r_i) | l, y)]`

The implementation will use a deterministic random seed per participant/trial
when estimating acquisition values so that adaptive choices are reproducible.
Tie breaks will prefer the shorter candidate length, reducing participant burden
when two candidates have indistinguishable information value.

## Simulation and analysis

The attempt will include a simulation or analysis script under `code/` that runs
synthetic participants with several fixed ability levels. The script will
compare adaptive and non-adaptive modes, record selected lengths over trials, and
show that the adaptive posterior moves toward different ability regions for
synthetic low-, medium-, and high-memory participants.

## Validation and evidence

Before finalizing the attempt, I will run:

- `python experiment.py` from the experiment directory;
- `psynet test local`;
- `psynet simulate` or the included standalone simulation script;
- the required performance test with JSON output under `evidence/`;
- participant-flow recording and screenshots using the repository evidence
  workflow;
- dashboard/data export artifacts required by the experiment evidence checklist.

The evidence will document any local environment blockers explicitly rather than
treating a skipped check as passing.
