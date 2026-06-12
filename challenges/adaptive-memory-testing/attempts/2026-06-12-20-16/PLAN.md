# Plan

## Science

The experiment will estimate each participant's latent digit-span-like memory ability from exact-recall responses. The core scientific requirement is efficient information gathering: each participant receives 10 digit-string trials, and the adaptive mode chooses each next string length to be maximally informative under the current posterior over the participant's ability. The response model follows the challenge specification:

- `l_0 = 8`
- `mu ~ Gamma(2, 2)`
- `alpha ~ Gamma(2, 1)`
- `r_i ~ Gamma(alpha, alpha / mu)`
- `p_ij = exp(-l_j / (l_0 * r_i))`
- `y_ij ~ Bernoulli(p_ij)`

Here `r_i` is participant memory ability, `l_j` is the selected digit-string length, and `y_ij` is exact-recall correctness. The model treats longer strings as harder and higher `r_i` as better memory.

## Methods

Participants will complete a short instruction page followed by 10 trials. Each trial has two pages:

1. Study page: show a generated digit string for a fixed short viewing duration.
2. Recall page: ask the participant to type the remembered digit string into a one-line text field.

Digit strings will be sampled uniformly from digits `0` through `9`, with the selected length stored alongside the generated target. Responses will be scored as correct only when the typed response exactly matches the target string. No partial-credit scoring will be used.

In adaptive mode, candidate lengths will be the integer range `2..20` inclusive, matching the non-adaptive random mode bounds. Before each trial, the policy will fit or update a variational posterior from the participant's completed trials. It will then estimate the expected information gain for each candidate length by:

- sampling plausible ability values from the current variational posterior;
- computing the response probability for each candidate length;
- considering the two possible outcomes, correct and incorrect;
- estimating how much the outcome is expected to reduce posterior uncertainty.

The selected trial will be the candidate length with the largest acquisition value. Ties will be resolved deterministically by choosing the shorter length, because shorter tied trials reduce unnecessary participant burden. When adaptive mode is disabled, each trial length will be sampled randomly and independently from `2..20` inclusive.

The analysis will demonstrate learning with synthetic participants at low, medium, and high abilities. It will compare selected lengths and posterior ability estimates across those synthetic participants, confirming that the policy chooses shorter strings for lower ability and longer strings for higher ability after observing evidence.

## Implementation

The experiment will be self-contained under `code/adaptive_memory_testing/` to avoid importing from a top-level directory named `code`. It will use PsyNet's static trial pattern:

- `MemoryTrial(StaticTrial)`: renders the study and recall pages, stores trial definitions, formats answers, and scores exact correctness.
- `AdaptiveMemoryTrialMaker(StaticTrialMaker)`: runs exactly 10 trials per participant and overrides trial preparation to choose or randomize the next length before the trial is shown.
- `Exp(Experiment)`: configures the timeline, bot behavior, simulation participant traits, and test settings.

### Participant timeline

The timeline will use standard PsyNet modules:

- `MainConsent()` for consent.
- `InfoPage` for task instructions.
- `AdaptiveMemoryTrialMaker` for the 10 memory trials.
- A short closing page if useful; otherwise PsyNet's successful end page can close the flow.

The trial UI will use `InfoPage` or a custom `ModularPage` for the study page and `ModularPage` with `TextControl(one_line=True, block_copy_paste=True)` for recall. The study page will display the target as large monospace text. The recall page will ask only for the digit string.

### Adaptive model module

The model code will live in a small local module, for example `adaptive_policy.py`, separate from the PsyNet page code. It will expose pure functions/classes that can also be used by simulation and analysis:

- `MemoryObservation(length: int, correct: bool)`
- `PosteriorState`: JSON-serializable variational parameters and diagnostics.
- `fit_posterior(observations, initial_state=None) -> PosteriorState`
- `expected_information_gain(state, candidate_length) -> float`
- `choose_length(observations, initial_state, adaptive=True, rng=None) -> SelectionResult`

Variational inference will approximate the participant-level posterior for `r_i`, with the population priors from the prompt fixed in the likelihood calculation. The initial implementation will use a log-normal variational approximation for `r_i` and optimize an evidence lower bound by Monte Carlo samples, using the previous trial's optimized parameters as the next trial's initialization. The cached state will include at least:

- variational family name;
- optimized location and scale parameters for `log(r_i)`;
- posterior mean and standard deviation for `r_i`;
- optimization status, objective value, and iteration count;
- candidate acquisition values for the selected trial.

The participant cache will be stored in `participant.var.adaptive_memory_posterior`. Each trial definition will also store a snapshot of the posterior state used for that trial, so the trial metadata can reconstruct what the policy knew before selection.

### Trial metadata

Each trial definition will include:

- `target`: generated digit string;
- `length`: selected string length;
- `adaptive`: whether adaptive mode was enabled;
- `candidate_lengths`: the considered candidate bounds/list;
- `posterior_state`: cached posterior state before the trial;
- `acquisition_values`: acquisition value for each candidate;
- `selected_acquisition_value`: acquisition value of the selected length;
- `selection_reason`: `adaptive_max_eig` or `random_nonadaptive`.

Each completed trial will store the raw response through PsyNet's normal answer field and an exact-match score. Additional derived metadata needed for analysis will be written in export-friendly JSON fields.

### Configuration

Adaptive mode will be easy to disable with a single experiment config value or environment variable, for example:

- `ADAPTIVE_MEMORY_MODE=adaptive` by default.
- `ADAPTIVE_MEMORY_MODE=random` for non-adaptive random lengths.

The candidate length bounds will be named constants:

- `MIN_SEQUENCE_LENGTH = 2`
- `MAX_SEQUENCE_LENGTH = 20`
- `N_TRIALS = 10`
- `L0 = 8`

### Bot simulation

Bots will receive latent memory abilities in `initialize_bot`. The recall control's bot response will generate correct or incorrect answers using the same response probability `exp(-length / (L0 * ability))`. Correct bot responses will return the target exactly; incorrect bot responses will return a same-length random digit string that is not equal to the target. Test/simulation settings will include enough bots to produce analyzable adaptive trajectories.

### Analysis and evidence after approval

After plan approval and implementation, the attempt will collect:

- `psynet test local` output for functional validation.
- Participant-flow screenshots and `evidence/participant.mp4` using the record-participant-video workflow.
- `evidence/performance.json` from `psynet performance-test local`.
- `evidence/simulated_data.zip` from `psynet simulate`.
- `evidence/analyses/analysis.ipynb` that directly reads exported CSV files, displays tables/plots, and interprets adaptive learning for synthetic low, medium, and high abilities.
- `REPORT.md` summarizing implementation, simulation, analysis, validation, and limitations.

### Risks and review questions

- The variational approximation must be light enough to run inside trial preparation without slowing participant flow. The posterior cache and warm start are intended to keep this manageable.
- The exact expected information gain calculation may be expensive if every candidate refits two hypothetical posteriors. If necessary, the implementation will use a bounded Monte Carlo approximation and document the approximation in code and report.
- Reviewer feedback is especially useful on whether the variational posterior should model only participant `r_i` online, or whether online updates should also approximate uncertainty in `mu` and `alpha` for a single-participant attempt.
