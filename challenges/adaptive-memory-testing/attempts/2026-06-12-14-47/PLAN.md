# Plan

## Science

The experiment estimates a participant-specific memory ability parameter from exact digit-string recall. The adaptive policy should concentrate trials near the string lengths where the participant is neither almost always correct nor almost always incorrect, because those trials carry the most information about the latent ability. The simulation will compare low-, medium-, and high-ability synthetic participants to show that selected lengths increase for stronger memories and decrease for weaker memories across ten trials.

## Methods

Participants will complete ten recall trials. On each trial, the page will display a randomly generated string of decimal digits for a fixed study interval, then ask the participant to type the string from memory. Responses will be normalized only by trimming surrounding whitespace; the score is correct if and only if the response exactly equals the target string.

The independent variable chosen by the adaptive policy is digit-string length. Candidate lengths are bounded to integers from 2 through 20 inclusive, matching the non-adaptive fallback requirement and avoiding strings too short or too long for review. When adaptive mode is disabled, each trial will choose a length uniformly at random from this same range. When adaptive mode is enabled, the next length will maximize expected information gain under the current variational posterior.

The response model will follow the public challenge specification:

- `l_0 = 8`
- `mu ~ Gamma(2, 2)`
- `alpha ~ Gamma(2, 1)`
- `r_i ~ Gamma(alpha, alpha / mu)`
- `p_ij = exp(-l_j / (l_0 * r_i))`
- `y_ij ~ Bernoulli(p_ij)`

For participant-facing trial metadata, every trial will save the selected length, target string, response, correctness, posterior state before the trial, posterior state after the trial, and the acquisition value used to select the length. The posterior state will be JSON-serializable so the trajectory can be reconstructed from exported data.

## Implementation

The attempt code will live in `code/adaptive_memory_testing/` to avoid importing from a directory named `code`. It will include a PsyNet experiment, a small adaptive inference module, tests or checks, and a simulation/analysis script.

The PsyNet experiment will use a custom `Trial` and a custom `TrialMaker` rather than a chain architecture. The `TrialMaker.prepare_trial(...)` method will read the participant's cached posterior state and history from `participant.var`, choose the next length, generate the target string, and return an available trial. The trial definition will include:

- `target`
- `selected_length`
- `adaptive_enabled`
- `posterior_before`
- `acquisition_by_length`
- `selected_acquisition`
- `candidate_lengths`

The custom trial will use a modular page with a digit-string prompt and a text input. `score_answer` will implement exact-match scoring. After each trial completes, the experiment will append `{length, target, response, correct}` to the participant history, fit the posterior using that history, and cache the result in `participant.var["memory_posterior_state"]`. The cached state will initialize the next fit, satisfying the trial-by-trial posterior reuse requirement.

The variational posterior will be a diagonal Gaussian over unconstrained parameters `log_mu`, `log_alpha`, and `log_r`. The inference module will transform samples back to positive space, add the log-Jacobian terms, and optimize a Monte Carlo evidence lower bound with NumPy/SciPy. This keeps the attempt self-contained while still using variational inference for the specified hierarchical model. The cached posterior state will contain means, log standard deviations, ELBO diagnostics, optimizer status, sample seed, and enough candidate-acquisition diagnostics to audit decisions.

The acquisition function will compute approximate expected information gain for every candidate length from 2 to 20. For each candidate, it will estimate the posterior predictive probability of a correct response, refit two hypothetical posteriors initialized from the current cache (`y=1` and `y=0`), and score the candidate as:

`H(q_current(log_r)) - E_y[H(q_next(log_r) | y, length)]`

The entropy proxy will use the log standard deviation of the variational `log_r` factor. This focuses adaptation on participant ability, while the hyperparameters remain part of the approximate posterior and likelihood.

Adaptive mode will be controlled by a single configuration constant/environment variable, defaulting to enabled. Disabling it will bypass posterior acquisition and sample uniformly from 2 through 20 while still scoring responses and saving posterior metadata.

The bot implementation will assign each synthetic bot a latent memory ability and respond correctly with probability `exp(-length / (8 * ability))`. Correct responses will echo the target string; incorrect responses will generate a different string of the same length. This bot path will be reused by the simulation script where possible.

## Validation and evidence plan

Before implementation is marked complete, run the experiment from the experiment directory with:

- `python experiment.py`
- `psynet test local`
- `psynet simulate`
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output <absolute evidence path>/performance.json`

Collect standard experiment evidence under `evidence/`: participant-flow video and screenshots, monitor snapshot, exported data zip, performance JSON or a blocker log, and analysis outputs. The simulation/analysis script will generate a machine-readable summary and plot/table showing selected lengths, correctness, and posterior ability estimates for synthetic participants with low, medium, and high memory ability.
