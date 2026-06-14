# Plan

## Science

The experiment estimates each participant's digit-span-like memory ability by choosing recall challenges that are maximally informative about that participant's latent ability. The observation `y` is binary exact-match recall correctness: `1` when the typed response exactly matches the target digit string and `0` otherwise. There are no planned participant-level covariates `z`; the hierarchical model pools information across participants through the population parameters `mu` and `alpha`.

The response model will follow the public specification using Gamma shape-rate priors and `l_0 = 8`:

- `mu ~ Gamma(2, 2)`
- `alpha ~ Gamma(2, 1)`
- `r_i ~ Gamma(alpha, alpha / mu)`
- `p_ij = exp(-l_j / (l_0 * r_i))`
- `y_ij ~ Bernoulli(p_ij)`

The adaptive policy will choose the next sequence length by estimating the expected information gain about the current participant's `r_i`. For each candidate length `l`, posterior samples from the variational approximation will be used to compute the binary mutual information `H(E[p(y=1 | r_i, l)]) - E[H(p(y=1 | r_i, l))]`. This avoids running a fresh variational fit for every hypothetical outcome while still optimizing a posterior expected information objective.

## Methods

Participants will complete 10 trials. On each trial, the experiment will show a string of random digits, then ask the participant to reproduce the string from memory in a text box. Copy/paste will be blocked for the recall response. A response will be scored as correct only when it is exactly equal to the target string.

Sequence lengths will be bounded to the public challenge range, 2 through 20 inclusive. In adaptive mode, every post-initial selection will evaluate all integer candidate lengths in that interval and choose the one with maximal expected information gain. The first trial will use the same policy with the prior/posterior predictive distribution; if the posterior fit is unavailable, it will fall back to the midpoint length with a recorded fallback reason. When adaptive mode is disabled, each trial length will be sampled uniformly at random from 2 through 20 inclusive.

The target digit string will be generated after the length is selected. Digits will be sampled uniformly and independently from `0` through `9`. The analysis will reconstruct target strings, responses, correctness, selected lengths, posterior snapshots, and acquisition values from exported trial metadata.

Synthetic participants for bots and standalone simulation will be assigned latent abilities `r_i`. Their recall correctness will be sampled from `Bernoulli(exp(-length / (8 * r_i)))`; correct simulated responses will reproduce the target exactly and incorrect responses will alter at least one digit while preserving an auditable response string. Simulation outputs will compare adaptive selection against the disabled random-length baseline for low, medium, and high ability values.

## Implementation

The runnable experiment will live under `code/adaptive_memory_testing/` to avoid importing directly from a package named `code`. It will start from PsyNet's chain-trial patterns and use a within-participant chain with one chain per participant, one trial per node, and `max_nodes_per_chain = 10`.

Core files:

- `experiment.py`: PsyNet experiment, chain node, chain trial, trial maker, pages, scoring, bot behavior, and validation hooks.
- `adaptive_logic.py`: hierarchical model log densities, variational posterior representation, fitting, sampling, acquisition scoring, and random-policy fallback.
- `simulate_procedure.py`: standalone synthetic simulation comparing adaptive and random policies, timing posterior fitting and design selection.
- `analysis.py` or notebook helper code: reusable export-reading and summary functions for the canonical notebook.

The trial UI will use a two-page PsyNet trial: an `InfoPage` for the digit string followed by a `ModularPage` with `TextControl` for recall. `score_answer` will write exact-match correctness to `trial.score`.

Adaptive selection will be attached to PsyNet's chain growth rather than overriding managed trial preparation. The next node definition will be created after completed trials are available, using `ChainNode.make_next_definition` or the closest current PsyNet chain hook. Each node definition will contain:

- `target_string`
- `selected_length`
- `adaptive_enabled`
- `candidate_lengths`
- `acquisition_values`
- `acquisition_value`
- `posterior_snapshot_id`
- `posterior_summary`
- `posterior_data_hash`
- `policy_version`
- `selection_elapsed_ms`
- `fallback_reason`

For queryable audit fields, the trial or node classes will use PsyNet field patterns such as `claim_field` for selected length, correctness, acquisition value, and posterior snapshot ID. Raw answers will remain available in standard PsyNet trial exports.

The posterior strategy will be `warm_start_from_previous_posterior`: each fit will include all finalized, non-failed relevant observations, but initialize the optimizer from the latest persisted posterior snapshot when the observation set matches or extends that snapshot. The cache will be represented by a custom persisted `PosteriorSnapshot` table with JSON columns for variational means, log scales, participant index mapping, optimizer diagnostics, observation count, observation hash, and timing. Stale snapshots will be treated only as initialization hints, not as proof that data has already been incorporated.

Variational inference will use a mean-field approximation over unconstrained log parameters for `mu`, `alpha`, and participant abilities `r_i`, with transformations back to the positive scale. The implementation will prefer NumPy/SciPy to avoid adding a probabilistic programming dependency unless local validation shows the optimizer is too brittle. The ELBO estimator will be deterministic under fixed seeds for tests and will expose timing logs for posterior fitting and acquisition scoring.

Validation will include:

- `python experiment.py`
- `psynet test local`
- `psynet simulate`, saving `evidence/simulated_data.zip`
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output <attempt>/evidence/performance.json`
- Playwright-driven participant evidence following `record-participant-video`
- The canonical executed notebook at `evidence/analyses/analysis.ipynb`, showing adaptive learning from synthetic participants of different abilities
- `REPORT.md` summarizing implementation, simulation, analysis, validation, and known limitations

## Human review questions

- Should the implementation keep the planned no-covariate `z = {}` design, or should any participant-level metadata be included in the model?
- Is the proposed mutual-information approximation acceptable for expected information gain, or should the implementation use nested posterior refits for each candidate and hypothetical outcome despite the response-path cost?
- Should adaptive mode default to enabled for participants, with the random-length mode exposed through a config flag for tests and comparisons?
