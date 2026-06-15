# Report

## Implementation summary

This attempt adapts PsyNet's original Gibbs demo from `~/PsyNet/demos/experiments/gibbs` while preserving the participant-facing task: each trial presents a target word and an RGB color state, and the participant adjusts only the active RGB channel while the other two channels remain fixed. The original target words, two Gibbs participant groups, across-chain Gibbs trial maker, start nodes, repeat trials, participant group selection page, color slider template, async post-trial hook, and export-regression coin table remain recognizable.

The implementation adds a second participant-level bot profile assignment for local simulation. `Exp.initialize_bot` assigns each bot from a seed-shuffled balanced roster containing five `random` and five `normal_rgb` labels. The profile is stored in `participant.var.bot_profile`, remains stable across all color and repeated trials, and is independent of the participant's Gibbs group.

The color-slider bot response now routes through PsyNet's native `SliderControl.bot_response` path. The `random` profile samples a uniformly random integer in `[0, 255]`. The `normal_rgb` profile samples the active channel from a normal distribution centered on the displayed starting channel, then rounds and clips to `[0, 255]`. Trial metadata records the profile, participant id, Gibbs group, target word, active color channel, starting RGB vector, submitted channel response, and distance from the starting channel.

The original network capacity was too small for a 10-bot run, so `max_nodes_per_chain` was increased while preserving the across-chain Gibbs structure. This prevents network depletion during the required 10-bot profile simulation and the 40-bot performance check.

## Validation and evidence

- `python experiment.py` was used as a launch/import check.
- `psynet test local` passed with exactly 10 completed bots.
- `evidence/profile_distribution.json` records the observed 5/5 distribution from the local 10-bot test run.
- `psynet simulate` passed and produced `evidence/simulated_data.zip`.
- `evidence/profile_distribution_simulate.json` records the observed 5/5 distribution from the simulation/export run.
- `evidence/analyses/analysis.ipynb` reads `evidence/simulated_data.zip` directly, checks profile and metadata invariants, and summarizes a lightweight behavioral comparison.
- `evidence/performance.json` records a 40-bot, 5-minute `psynet performance-test local` run with zero bot errors.
- `evidence/monitor.html` contains a profile-colored monitor dashboard generated
  from the simulated export. It preserves the Gibbs experiment structure as
  network -> Gibbs node -> trial, colors trial nodes by the participant profile,
  and provides clean click-through details for networks, nodes, and trials.

## Simulation results

Both the local test run and the simulation/export run observed exactly five completed `random` bots and five completed `normal_rgb` bots. Each profile contributed 35 completed color trials, corresponding to seven finalized Gibbs trials per participant including repeats. All exported submitted channel responses were integers in the valid inclusive range `[0, 255]`, and each participant kept a single profile across all color trials.

The analysis notebook shows the intended sanity-check distinction between profiles: the `random` profile spans a wide response range, while `normal_rgb` responses stay closer to the displayed starting channel on average. These are bot-profile diagnostics only and should not be interpreted as human perceptual behavior.

## Limitations

No production services, recruiter credentials, or external APIs were used. Participant video was not collected because the implementation changes bot scheduling, bot response generation, and export metadata while leaving the original Gibbs participant interface intact; the interface was exercised through PsyNet's bot-rendered local flow and represented by the profile monitor dashboard.
