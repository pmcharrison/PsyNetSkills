# Report

## Summary

This attempt adapts PsyNet's Gibbs demo so that local simulated participants receive stable response profiles while preserving the original color-word Gibbs task. Bots still choose participant group `A` or `B`, see a target word, view an RGB state, and submit the active RGB channel through the original slider response path.

## Implementation

- The runnable experiment is in `code/gibbs_bot_profile_simulation/`.
- `Exp.initialize_bot` assigns each bot a stable `participant.var.bot_profile` from a shuffled balanced roster.
- The 10-bot test roster contains five `random` profiles and five `normal_rgb` profiles.
- The `random` profile samples a uniformly random valid RGB-channel integer.
- The `normal_rgb` profile samples a clipped integer from a normal distribution centered on the presented active-channel value with standard deviation 20 RGB units.
- The slider bot response returns a PsyNet `BotResponse`, so simulated participants use the same response submission path as ordinary participants.
- Export-visible metadata records participant id, profile, target word, active channel, starting RGB vector, and submitted channel response in participant, trial, and response exports.

The original participant-group behavior remains separate from response profile assignment. The only scheduling change is increasing `trials_per_node` from 2 to 3 so all 10 required bots can complete the original four normal Gibbs trials plus three repeat trials.

## Evidence

- `evidence/simulated_data.zip` contains the exported simulated PsyNet run.
- `evidence/profile_distribution.md` reports the observed completed-participant profile distribution from `Bot.csv`.
- `evidence/profile_distribution.csv`, `evidence/profile_stability.csv`, and `evidence/behavioral_comparison.csv` provide compact tabular summaries.
- `evidence/analyses/analysis.ipynb` reads the exported CSVs directly and embeds tables, plots, and interpretation.
- `evidence/performance.json` contains the 5-minute local performance-test output.
- `evidence/monitor.html` contains a local PsyNet dashboard monitor snapshot.

Observed completed-participant profile distribution:

| bot_profile | completed_participants |
| --- | ---: |
| normal_rgb | 5 |
| random | 5 |

All 10 simulated participants completed the flow. Each participant kept one profile across all seven finalized color trials, and all submitted channel responses were integers in the inclusive range 0 to 255.

## Validation

- `python experiment.py` passed.
- `psynet test local` passed with 10 serial bots.
- `psynet simulate` passed and produced the exported evidence.
- `jupyter nbconvert --to notebook --execute --inplace analysis.ipynb` passed.
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output evidence/performance.json` completed with zero bot errors and zero request errors.
- `uv run psynetsk-validate` passed.

## Limitations

The behavioral comparison is a simulation sanity check only. It validates that profile plumbing and exports work locally; it is not evidence about real participant behavior.
