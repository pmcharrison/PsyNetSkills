# Plan

## Science

This attempt is a simulation-validation adaptation of PsyNet's Gibbs color demo, not a new scientific task. The scientific task remains the original Gibbs-sampling workflow: participants see a target word, view an RGB state, and adjust the active RGB channel while the other two channels are fixed. The adaptation adds local simulated participant profiles so reviewers can verify that bot behavior, metadata, and exported responses are distinguishable without interpreting bot outputs as human perceptual data.

## Methods

The experiment will retain the Gibbs demo's target words (`tree`, `rock`, `carrot`, `banana`), RGB color channels, two participant groups (`A`, `B`), across-chain Gibbs trial maker, start nodes, repeat trials, and participant group selection page. Each simulated participant will first receive the usual Gibbs participant group through the existing group-choice page, preserving the demo's network and target-word scheduling behavior.

A second participant-level assignment will define the simulated response profile. For the local test run, the scheduler will build a balanced roster with five `random` and five `normal_rgb` profile labels, shuffle it with a run seed, and assign one profile to each bot during bot initialization. The profile will be stored in `participant.var.bot_profile` and will remain stable for the participant's full trial sequence, including repeated Gibbs trials. The profile assignment will not be derived directly from the numeric participant id; ids will only index or claim entries from the shuffled balanced roster.

The `random` profile will submit uniformly sampled integer active-channel values over the inclusive range 0-255, independent of target word and starting RGB state. The `normal_rgb` profile will submit a locally stochastic integer active-channel value sampled from a normal distribution centered on the presented starting active-channel value, then rounded and clipped to 0-255. Trial-level metadata will expose the bot profile, participant id, target word, active channel, starting RGB vector, and submitted active-channel response so the export connects each response to the profile that generated it.

Behavioral comparison will be limited to simulation sanity checks. The analysis will report completed-participant profile counts, response ranges for `random`, and response distance from the presented starting channel for `normal_rgb`, with clear labeling that these are bot-profile diagnostics rather than evidence about real human behavior.

## Implementation

The attempt code will live under `code/gibbs_bot_profile_simulation/` to avoid importing the directory as Python's standard-library `code` module. I will copy the original Gibbs demo support files needed by PsyNet local checks, including `experiment.py`, `test.py`, `config.txt`, templates, Docker/update scripts as appropriate, and the demo `.gitignore`.

In `experiment.py`, I will keep the existing `ColorSliderPage`, `CustomNetwork`, `CustomTrial`, `CustomNode`, `CustomTrialMaker`, `trial_maker`, coin table, participant-group page, and experiment timeline recognizable. I will refactor the slider bot response into profile-aware helpers that receive the selected channel and starting RGB values, look up the current bot participant's assigned profile, and return the same answer format expected by `SliderControl`/`ColorSliderPage`. The helper will include explicit clipping and integer conversion for both profiles.

Profile assignment will be implemented on the experiment class through PsyNet's bot lifecycle, preferring an `initialize_bot` override if available in the current PsyNet API. The override will delegate to `super()` first, create or reuse a shuffled balanced profile roster for exactly ten test bots, set `participant.var.bot_profile`, and record a seed/run identifier in participant vars. If the refreshed PsyNet API exposes a more idiomatic bot-initialization hook, I will use that hook while preserving the same participant-var and export-visible behavior.

Trial metadata/export support will be added close to the trial/page code. The trial or page metadata will include `bot_profile`, `target`, `active_channel`, `active_index`, `starting_values`, and the validated submitted active-channel response. I will use PsyNet's normal answer-saving path and will not write simulated answers directly into exported data or bypass trial validation.

The local test phase will set `Exp.test_n_bots = 10`. `Exp.test_check_bots` will verify that all ten bots complete the expected Gibbs trial flow, exactly five completed participants have `random`, exactly five have `normal_rgb`, each participant has a stable profile across all color trials, all submitted channel responses are integer values in 0-255, and profile metadata is present in export-ready trial or answer data. The test will also print or write an observed profile-distribution summary for evidence.

Evidence collection after implementation will follow the experiment-implementation checklist: `python experiment.py`, `psynet test local`, `psynet simulate` with a saved `evidence/simulated_data.zip`, a canonical executed `evidence/analyses/analysis.ipynb` reading exported CSV files directly, `REPORT.md`, and performance evidence or a clearly documented blocker. I will also record targeted participant-flow evidence only if needed to demonstrate participant-facing behavior beyond what the original Gibbs demo already shows.

## Review gate

Implementation is paused here because the challenge workflow requires human review of `PLAN.md` before coding. The reviewer should confirm whether this plan preserves the original Gibbs task while adding the requested balanced bot-profile simulation, or provide corrections before implementation continues.
