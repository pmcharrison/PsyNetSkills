# Learnings

## Criteria-sized adaptive simulations can exhaust JAX memory

The 30-adaptive-participant simulation initially failed with JAX/LLVM memory allocation errors because repeated VI fits accumulated compiled artifacts in one process. Running each adaptive participant simulation in a short-lived child process released JAX memory and allowed the criteria-sized simulation to complete.

*Actions:*

- **PsyNetSkills:** Update adaptive challenge or skill guidance to recommend isolating large JAX/NumPyro simulation batches by participant or chunk when repeated VI compilation is expected. Confidence: high. Impact: medium. Status: considering.

## Adaptive policy accuracy needs explicit baseline checks

The first adaptive policy satisfied the mechanics of adaptive selection but did not outperform random selection in the HMC accuracy comparison. The hidden criteria made the baseline comparison explicit and revealed that a working adaptive loop is not enough evidence of scientific value.

*Actions:*

- **PsyNetSkills:** Add public challenge guidance that adaptive implementations should compare posterior recovery against a non-adaptive baseline before considering the attempt successful. Confidence: high. Impact: medium. Status: considering.
