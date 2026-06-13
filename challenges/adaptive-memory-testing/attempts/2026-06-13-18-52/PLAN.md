# Plan

## Science

The experiment will estimate each participant's short-term digit-span ability using 10 exact-recall trials. The latent participant ability `r_i` controls the probability of exactly recalling a presented digit string through `p_ij = exp(-l_j / (8 * r_i))`, so longer strings are more diagnostic for higher-ability participants and shorter strings are more diagnostic for lower-ability participants. The adaptive policy will choose each new string length to maximize expected information gain about the current participant's `r_i`, while sharing population-level information through `mu` and `alpha`.

## Methods

Participants will first read brief instructions explaining that each trial shows a digit string, hides it, and then asks for exact reproduction. Each participant will complete 10 main trials. On trial `j`, the experiment will select a length `l_j` between 2 and 20 inclusive, generate a random digit string of that length, present it briefly in a large monospace display, then show a one-line text response box with copy/paste disabled. A response will be scored correct only if the submitted string exactly matches the target.

The default condition will be adaptive. Before each trial, the policy will fit or update an approximate posterior for the hierarchical Gamma-Bernoulli model using all finalized trials available up to that point. Candidate lengths will be the full integer grid 2-20, matching the non-adaptive range and the public challenge bounds. The acquisition function will estimate expected information gain by comparing the current posterior entropy for the participant ability with the expected posterior entropy after possible Bernoulli outcomes at each candidate length. When adaptive mode is disabled by configuration, each trial length will instead be sampled uniformly from 2-20 and the same metadata will still be recorded with `adaptive=false`.

Bots will simulate synthetic participants by sampling or assigning an ability `r_i`, responding correctly with probability `exp(-l_j / (8 * r_i))`, and otherwise returning an incorrect digit string. The simulation evidence will include low-, medium-, and high-ability synthetic participants to demonstrate that selected lengths move upward for stronger memory and downward for weaker memory.

## Implementation

The runnable experiment will live in `code/adaptive_memory_testing/` to avoid importing from a directory named only `code`. It will use a `StaticTrialMaker` subclass with `expected_trials_per_participant=10`, `max_trials_per_participant=10`, `allow_repeated_nodes=True`, and one `StaticNode` per candidate length. A custom `AdaptiveMemoryTrialMaker.prioritize_networks(networks, participant, experiment)` will rank the length networks for the participant. This uses PsyNet's allocation hook rather than overriding `prepare_trial`.

The trial class will subclass `StaticTrial`. `finalize_definition` will generate the target digit string, attach the selected length, adaptive-mode flag, posterior snapshot summary, acquisition value, candidate acquisition values, data cutoff, optimizer/model versions, and timing values. `show_trial` will return a short timeline: present the target string, then solicit a text response. `score_answer` will map the raw answer to `y = 1` only for an exact match and `0` otherwise, keeping the raw answer available for audit. Queryable/exported metadata will use `claim_field` where appropriate for selected length, target string, response, correctness `y`, acquisition value, posterior id/version, posterior mean/sd for `r_i`, and timing; compact candidate arrays and posterior parameters can live in serialized dict/list fields.

Core adaptive calculations will live in `adaptive.py`: hierarchical model constants, variational fitting, posterior cache structures, posterior predictive calculation, EIG scoring, and synthetic participant helpers. I will use NumPyro for variational inference because the prompt requires VI and the model is hierarchical. The posterior update strategy will be `warm_start_from_previous_posterior`: each participant's latest posterior parameter snapshot will be cached in queryable trial fields and reused to initialize the next VI fit, while fitting still incorporates all finalized trials for that participant and relevant population observations to avoid silently skipping data. The cache representation will include model version, optimizer version, data cutoff, VI parameters, posterior summary, fit diagnostics, and elapsed timing.

A small `simulate_procedure.py` will run the adaptive policy outside PsyNet against static random-length baselines for several synthetic abilities, checking posterior recovery and selection timing. The PsyNet experiment will also expose `Exp.test_n_bots` high enough for `psynet simulate` to export a representative dataset. The analysis notebook at `evidence/analyses/analysis.ipynb` will read the simulated export CSVs directly, summarize trial correctness by participant and selected length, plot length trajectories by synthetic ability, and report posterior recovery diagnostics.

Validation will run from the experiment directory: `python experiment.py`, `psynet test local`, `psynet simulate` with export saved to `evidence/simulated_data.zip`, the standalone simulation script, the canonical notebook, and `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output <absolute evidence path>/performance.json` if the local PsyNet services support it. Participant-facing evidence will be collected with Playwright plus ffmpeg under `evidence/screenshots/` and `evidence/participant.mp4`, keeping the video under 3 minutes and 1280x720.

## Review questions

- Please confirm the human author GitHub key to place in `agent.json`. Existing keys are listed in `authors.yaml`.
- Please confirm that the proposed NumPyro VI dependency is acceptable for this challenge implementation.
- Please confirm that the adaptive unit should be digit-string length only, with no participant covariates `z` beyond the participant identity and accumulated responses.
