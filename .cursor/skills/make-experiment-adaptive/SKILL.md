---
name: make-experiment-adaptive
description: Convert an existing PsyNet experiment into an adaptive experiment with model-based trial or network selection.
authors: [lucasgautheron]
---

# Make a PsyNet experiment adaptive

Use this skill when asked to make an existing PsyNet experiment adaptive,
including Bayesian adaptive design, active inference, Thompson sampling, or
another policy that selects future trials from data already collected.

## Required reads

- Read `psynet-experiment-implementation/SKILL.md` for the general experiment
  workflow and validation expectations.
- Read `simple-round-structure/SKILL.md` before changing the trial, node, or
  network architecture.
- Read `psynet-deployment-ops/SKILL.md` when persistence, deployment,
  recruitment, or exported data safety matters.
- Inspect the closest existing experiment and the current PsyNet trial-maker
  implementation before coding. In PsyNet, prefer selection hooks such as
  `prioritize_networks`; do not override `prepare_trial`.

## Specification gate

Do not implement an adaptive experiment until the user supplies the specification
below, unless they explicitly ask you to propose a design. If anything is
missing, list the decisions they must make and wait for their answer.

- `y`: the mapping from raw trial answers to model observations.
- `z`: the mapping from participant or context data to model covariates.
- Adaptive unit: what the policy selects, such as a network, node, condition,
  stimulus, item, block, or trial family.
- Generative model: likelihood, latent parameters, priors, and how `y`, `z`,
  and the adaptive unit enter the model.
- Posterior strategy: how posterior beliefs are fit or sampled.
- Optimization policy: objective and decision rule, such as EIG, expected free
  energy, Thompson sampling, greedy utility, or an early-stopping rule.
- Persistence requirement: whether posterior state should persist or be
  recomputed without durable posterior storage.
- Dependency preference or constraints, if any.

If the user asks for suggestions, make the smallest coherent proposal and label
which choices are assumptions.

## Implementation constraints

- Use `y` for trial-level observations and `z` for participant or context
  covariates throughout adaptive code, logs, and exports.
- Ask for or implement explicit mapping logic from raw answers to `y`, and from
  participant/context data to `z`.
- Prefer custom persisted attributes for core adaptive variables (`y`, `z`,
  objective values, posterior snapshot IDs) over ad hoc JSON var storage. Use
  PsyNet field patterns such as `claim_field` when the value deserves a real
  queryable/exported column. Use vars only for small, incidental metadata.
- Keep raw answer data available for audit; do not replace it with only `y`.
- Log each adaptive decision: candidate IDs, chosen ID, objective components,
  posterior version or snapshot, data cutoff, and optimizer version.
- When already computed at no extra approximation cost, store the posterior
  predictive summary for `y` as it was used when delivering the trial. For
  binary or other low-dimensional discrete `y`, store the probability mass
  function as a list; for continuous `y`, store only the predictive mean and
  standard deviation. Do not add extra integrals, sampling, or approximation work
  just to produce this record.
- Make the adaptive path deterministic under a fixed seed where possible, or
  explicitly record random seeds for stochastic policies.
- Keep selection code fast enough for the participant response path. Adaptive
  computation should normally take less than 1 second per selection; treat
  roughly 2 seconds halfway through an actual deployment as a warning threshold
  that requires simplification, caching, or a different posterior strategy.
- Add timing logs around data loading, posterior fitting/sampling, and objective
  scoring.
- If bot_response logic is not already supplied, override the default with answers
drawn from the generative model itself
- Lower-level computational logic (such as Bayesian computations) should be located in
a separate file (`adaptive.py`) imported from `experiment.py` and any other script
that needs these procedures.
- Implementations should include a concise standalone simulation script (`simulate_procedure.py`) that:
   - Simulates the adaptive setup against a static baseline outside psynet,
   on a reasonable number of participants. 
   - If an approximate inference scheme is used, check the accuracy of posterior estimates
   in these simulations, using less approximate inference strategies such as HMC.
   - Produces diagnostic plots, in particular posterior predictive checks,
   to confirm that Bayesian computations are reliable.

## Posterior update strategy

Choose one of these strategies explicitly:

1. `from_scratch`
   - Recompute the posterior from all finalized, non-failed relevant trials.
   - Prefer this for correctness, reproducibility, and concurrent participants.
   - Use sufficient-statistic queries or cached immutable data when possible.

2. `warm_start_from_previous_posterior`
   - Initialize fitting from the last persisted posterior, but include all data
     needed to avoid missing observations.
   - Persist posterior snapshots in the database using an appropriate custom
     table, including model version, optimizer version, data cutoff, fit status,
     diagnostics, and timestamp.
   - Treat stale snapshots as hints, not proof that data has been incorporated.

3. `online_learning`
   - Avoid by default. Updating from only new data plus the previous posterior can
     silently discount data when concurrent workers start from stale snapshots.
   - Use it only with a single-writer queue, explicit locks, or another auditable
     mechanism proving every observation is incorporated exactly once.

## Dependency selection

- Match dependencies to the chosen model and policy, balancing performance,
  clarity, deployment cost, and future extensibility.
- Prefer NumPy/SciPy for conjugate models, closed-form sufficient statistics,
  simple Beta-Bernoulli or Gaussian updates, and lightweight bandit policies.
- Prefer a probabilistic programming library when the model is hierarchical,
  non-conjugate, likely to evolve, or needs reusable posterior predictive
  simulation. Pyro is appropriate for complex VI/EIG designs but is heavy.
- Do not add Pyro, Stan, PyMC, or similar dependencies just to compute simple
  closed-form objectives.
- If adding dependencies, pin or constrain them using the experiment's normal
  dependency workflow and verify local and deployment compatibility.

## Validation

- Run bot tests or simulations that exercise the adaptive selection path, not
  just the static participant flow.
- Export or query trial data and verify that `y`, `z`, selected adaptive units,
  posterior references, objective components, and any free posterior predictive
  summaries are present.
- Check that repeated runs with a fixed seed reproduce the same decisions when
  the policy is intended to be deterministic.
- Stress the concurrent case with multiple bots when participants may overlap.
- Review timing logs and fail the design if posterior fitting, objective
  scoring, or DB scans exceed the real-time budget for the participant response
  path.

## Common failures

- Proceeding before the user has specified `y`, `z`, model, posterior strategy,
  policy, and persistence needs.
- Recomputing from every trial with expensive probabilistic programming code
  without timing or scalability checks.
- Storing core adaptive state only in JSON vars when it should be queryable,
  versioned, or exported as a first-class field.
- Using online learning without concurrency protection.
- Overriding PsyNet's managed trial preparation logic instead of using the
  appropriate selection hook.
