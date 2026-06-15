# Report

## Implementation

Implemented a self-contained PsyNet experiment in `code/adaptive_memory_testing/`. Participants complete 10 digit-string exact-recall trials. Trial length is selected from 2-20 using an adaptive policy in `adaptive.py`; disabling adaptive mode with `ADAPTIVE_MEMORY_ADAPTIVE=0` switches to random lengths over the same range.

The experiment records target string, raw response, exact-match `y`, participant covariate `z`, selected length, acquisition values, posterior snapshot metadata, posterior predictive probabilities, model/optimizer versions, and timing fields on each `MemoryRecallTrial` export row.

## Simulation and analysis

`simulate_procedure.py` generates 30 adaptive and 30 non-adaptive synthetic participants. The analysis fits the hierarchical Gamma-Bernoulli model with NumPyro NUTS/HMC and writes `evidence/standalone_simulation/hmc_accuracy_comparison.csv`.

In the completed simulation, the adaptive policy selected shorter strings for low synthetic ability and longer strings for higher synthetic ability. The HMC comparison reported mean absolute error of 2.5594 for adaptive participants and 1.6519 for non-adaptive participants, so this particular adaptive policy did not outperform the random baseline on ability-estimate accuracy.

## Validation

Functional PsyNet bot validation passed with 12 serial bots, each completing the 10-trial flow. Playwright completed a participant flow and produced screenshots plus `evidence/participant.mp4`. `psynet simulate` exported 120 `MemoryRecallTrial` rows to `evidence/simulated_data.zip`, and `evidence/analyses/analysis.ipynb` reads that export directly.

The 40-bot, 5-minute performance test completed and wrote `evidence/performance.json`, but it is a warning result: no bots completed within the five-minute window, median response time was 0.914 s, p95 response time was 14.187 s, and request errors were observed. The main pressure point is repeated VI fitting in the participant response path under high concurrency.

## Remaining issues

- Human author metadata is still pending in `agent.json`.
- The adaptive policy satisfies the implementation requirements but does not yet improve HMC ability-estimate accuracy over the random baseline in the criteria-sized synthetic simulation.
- The VI path is functional for ordinary bot flows but too slow for the sustained 40-bot performance target.
