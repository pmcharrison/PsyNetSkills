# Plan

## Science

The experiment estimates an individual participant's digit-span-like memory
ability while minimizing wasted trials. Each response is reduced to a binary
observation `y`: `1` when the typed recall exactly matches the presented digit
string and `0` otherwise. There are no participant-level covariates `z` in the
initial implementation. The adaptive unit is the next digit-string length.

The response model will follow the challenge specification:

- `mu ~ Gamma(2, 2)`
- `alpha ~ Gamma(2, 1)`
- `r_i ~ Gamma(alpha, alpha / mu)`
- `p_ij = exp(-l_j / (8 * r_i))`
- `y_ij ~ Bernoulli(p_ij)`

The adaptive policy will use the current variational posterior to estimate the
mutual information between the next binary response and the latent memory
ability. Higher-ability synthetic participants should be assigned longer strings
over time, lower-ability participants should be assigned shorter strings, and
the analysis should show that these trends separate across simulated ability
levels.

## Methods

Participants will complete 10 trials. Each trial will first display a random
digit string, then prompt the participant to reproduce it from memory using a
single-line text input. The response will be scored as correct only after exact
string comparison against the target. Digit strings will be sampled uniformly
from `0`-`9` at the selected length, allowing repeated digits.

In adaptive mode, before each trial the experiment will fit or update a
variational posterior from all completed trials for the participant. The policy
will evaluate every integer candidate length from 2 to 20 inclusive and choose
the length with the largest expected information gain about `r_i`. These bounds
match the public challenge's random-mode range and keep the participant-facing
stimuli plausible. On ties, the shorter length will be chosen to reduce
participant burden.

In non-adaptive mode, the same participant workflow and scoring logic will run,
but each trial length will be sampled uniformly from 2 to 20 inclusive. This
mode will be controlled by a single experiment setting or environment variable
so reviewers can disable adaptation without editing trial logic.

Synthetic bots will represent low, medium, and high memory abilities. On each
trial a bot will recall correctly with probability `exp(-length / (8 * r_i))`;
incorrect responses will be same-length digit strings that differ from the
target. Simulation outputs will compare selected lengths, correctness, posterior
ability estimates, and acquisition values across ability levels.

## Implementation

The runnable experiment will live under `code/adaptive_memory_experiment/` to
avoid importing a package named `code`. It will be based on PsyNet's
within-participant chain pattern:

- `MemoryChainNode(ChainNode)` will own the state used to generate the next
  trial definition. `make_next_definition` will read
  `completed_and_processed_trials`, rebuild the participant's observation
  history, warm-start the posterior fit from the previous cached state, evaluate
  candidate lengths, and return the next definition.
- `MemoryTrial(ChainTrial)` will present the digit string with `InfoPage`, then
  collect recall with `ModularPage` and `TextControl`. `format_answer` will trim
  whitespace, and `score_answer` will return `1` only for an exact match.
- `ChainTrialMaker` will use `chain_type="within"`,
  `chains_per_participant=1`, `trials_per_node=1`, `max_nodes_per_chain=10`,
  `max_trials_per_participant=10`, and
  `expected_trials_per_participant=10`.
- The experiment timeline will include consent/instructions, the trial maker,
  and a concise final page.

Adaptive computations will be isolated in `adaptive_logic.py` so the PsyNet
experiment, standalone simulations, and notebook all use the same model code.
The initial posterior strategy will be `warm_start_from_previous_posterior`:
each fit will include all completed observations for correctness, but initialize
the optimizer from the most recent posterior state. The posterior cache will be
a JSON-serializable object containing the variational means/scales on the
unconstrained log-parameter scale, optimizer metadata, candidate scores, timing
metadata, and model version. The state used to choose each trial will be stored
in the trial definition, and the next fit will use the prior state's parameters
only as an initialization hint.

The variational approximation will be a compact mean-field distribution over
unconstrained `log_mu`, `log_alpha`, and `log_r`. A deterministic random seed
will generate Monte Carlo samples for the ELBO and acquisition calculation so
bot tests can assert reproducible decisions. The acquisition value for a
candidate length will be estimated as:

`H(E_q[p(y=1 | length, r_i)]) - E_q[H(p(y=1 | length, r_i))]`.

Each trial definition will include:

- `target_string`
- `selected_length`
- `adaptive_mode`
- `candidate_lengths`
- `acquisition_values`
- `acquisition_value`
- `posterior_state`
- `posterior_cache_version`
- `selection_timing_ms`

The implementation will also expose key fields as queryable/exported trial
columns where practical, while preserving the raw `definition`, raw response,
and `score` for audit.

Validation will proceed in layers after plan approval:

1. Run a standalone `simulate_procedure.py` to verify the adaptive policy learns
   from low, medium, and high synthetic participants and to measure posterior
   fitting and selection timings.
2. Run `python experiment.py` from the experiment directory.
3. Run `psynet test local` and assert all bots complete exactly 10 trials.
4. Run `psynet simulate` and save the export as `evidence/simulated_data.zip`.
5. Execute `evidence/analyses/analysis.ipynb`, keeping it under the dashboard
   size limit while showing tables and plots directly from the exported CSVs.
6. Run the participant-flow recording workflow for `evidence/participant.mp4`
   and targeted screenshots.
7. Run the performance test and save `evidence/performance.json`, or record a
   concrete blocker in `EVALUATION.md`.
8. Write `REPORT.md` summarizing the implementation, simulations, analysis, and
   any unresolved validation issues.
