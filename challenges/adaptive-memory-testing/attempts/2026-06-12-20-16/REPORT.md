# Report

## Implementation

The attempt implements a self-contained PsyNet experiment in `code/adaptive_memory_testing/`. Participants complete 10 digit-string recall trials. Each trial presents a generated digit string, then asks for exact recall in a one-line text field. Responses are scored correct only when they exactly match the target.

The adaptive policy lives in `adaptive_policy.py`. It fits an independent log-normal variational posterior over `mu`, `alpha`, and participant-specific `r_i`, using the challenge's Gamma priors and Bernoulli recall likelihood. The previous posterior state is stored in `participant.var.adaptive_memory_posterior` and used as the starting point for the next variational optimization. Candidate lengths are bounded to integers 2 through 20 inclusive. Adaptive selection uses expected information gain under the current posterior; random mode can be selected with `ADAPTIVE_MEMORY_MODE=random`.

Each trial definition records the target, selected length, adaptive mode, candidate bounds, posterior state, posterior summary, acquisition values, selected acquisition value, and model metadata. The exported `MemoryTrial.csv` therefore contains enough information to reconstruct the target, response, correctness, selected length, posterior state, and acquisition value for each trial.

## Validation

The policy smoke test ran synthetic low, medium, and high ability participants through the same adaptive code path used by the experiment. `psynet test local` ran six serial bots through the full participant flow, and all bots completed 10 trials. `psynet performance-test local` ran a 40-bot, 5-minute load test with 0 bot errors and 0 request errors.

## Evidence

- `evidence/participant.mp4` shows the participant-facing ad, consent, representative study/recall pages, and successful completion.
- `evidence/screenshots/` contains targeted screenshots for the ad, study, recall, and completion states.
- `evidence/simulated_data.zip` contains a PsyNet simulation export with six synthetic bot participants spanning abilities 0.45, 0.7, 1.0, 1.4, 2.0, and 3.0.
- `evidence/data.zip` contains a local export of the final six-bot run.
- `evidence/performance.json` contains the 40-bot performance-test output.
- `evidence/analyses/analysis.ipynb` reads `simulated_data.zip` directly, summarizes metadata completeness and participant trajectories, and plots selected lengths and posterior `r_i` means.
- `evidence/monitor.html` contains a local dashboard snapshot.

## Findings

The simulation and analysis show the adaptive policy moving toward shorter strings for lower ability and longer strings for higher ability. All simulated trial rows record joint posterior metadata for `mu`, `alpha`, and `r_i`.

## Limitations

The public challenge instructions required variational inference and a synthetic-participant demonstration; the implementation follows those instructions. After implementation and first-pass evidence collection, the hidden evaluator criteria additionally requested 30 adaptive participants, 30 non-adaptive participants, and an HMC-based comparison of memory-ability estimate accuracy. Those criteria were copied into `EVALUATION.md` for human review but were not used to retrofit the implementation after hidden-criteria disclosure.
