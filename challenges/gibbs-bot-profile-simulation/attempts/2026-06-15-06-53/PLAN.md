# Plan

## Science

This attempt will preserve the original PsyNet Gibbs color-word sampling task while adding controlled simulated participant behavior for local validation. Participants will still choose a Gibbs participant group, see a target word, view an RGB state, and adjust only the active color channel on each Gibbs trial while the other two channels remain fixed. The added simulation profiles are not claims about real human color-word behavior; they are sanity-check profiles for validating the experiment's bot path and exported metadata.

## Methods

The experiment will adapt PsyNet's `~/PsyNet/demos/experiments/gibbs` demo into `code/gibbs_bot_profile_simulation/`. The task materials will remain the original target words (`tree`, `rock`, `carrot`, `banana`) and RGB channels (`red`, `green`, `blue`). The Gibbs networks, start nodes, participant groups, trial maker parameters, repeat trials, and participant group selection flow will remain recognizable from the demo unless a small change is needed for validation.

The simulated run will use exactly 10 local bots. A balanced roster containing five `random` and five `normal_rgb` profiles will be shuffled for each configured seed or run. Each participant will receive one profile from this roster at the start of the timeline, stored in `participant.var.bot_profile`, and keep that profile for all normal and repeat color trials. The roster will be independent from the existing Gibbs participant group, so participant group, network selection, and target-word scheduling remain separate from simulation behavior.

The two response profiles will behave as follows:

- `random`: submit a uniformly random integer in `[0, 255]` for the active RGB channel, independent of target word and presented RGB state.
- `normal_rgb`: submit a clipped integer sampled from a normal distribution centered on the presented active-channel value. The implementation will record enough context to compare the submitted response with the presented RGB state.

Trial/export metadata will connect every simulated color response to the participant id, `bot_profile`, target word, active channel, starting RGB vector, and submitted active-channel value. The participant profile distribution requested for evidence will be reported from completed simulated participants, not inferred from ids or expected roster size alone.

## Implementation

1. Copy the Gibbs demo support files into `code/gibbs_bot_profile_simulation/`, including `experiment.py`, templates, config files, `.gitignore`, and standard Dallinger/PsyNet support files needed by local launch checks.
2. Add constants for profile ids, bot count, optional simulation seed, and normal-profile standard deviation.
3. Add a balanced shuffled profile assignment function that creates five `random` and five `normal_rgb` slots for a 10-bot test run. The assignment will be stable per participant after it is written to `participant.var.bot_profile`.
4. Insert an early `CodeBlock` or equivalent timeline step after participant creation and before color trials to assign and persist the bot profile without changing the existing participant-group page semantics.
5. Replace the Gibbs slider's fixed random `bot_response` with a profile-aware response connected through PsyNet's page/control bot response mechanism. The response function will read the participant's stored profile, current trial metadata, selected active channel, and starting RGB vector, then return the same answer format the slider expects.
6. Extend `ColorSliderPage.metadata()` and/or `CustomTrial` post-trial metadata so exported trial data includes profile id, participant id, target word, active color channel, starting RGB vector, and submitted response. The exported data should not require answer-value heuristics to recover profile membership.
7. Set `Exp.test_n_bots = 10` and update `test_check_bots` to verify all 10 bots complete, profiles are exactly 5/5 among completed participants, profiles remain stable across all color trials, responses are integers in `[0, 255]`, and profile metadata is export-visible.
8. Add a small analysis/report script if useful for evidence extraction from the simulated export. It will print and write the observed participant profile distribution, including counts by profile from completed participants.

## Testing and evidence plan

Success requires runtime evidence from the adapted experiment, not code inspection alone. After plan approval and implementation, I will run these checks from `code/gibbs_bot_profile_simulation/`:

- `python experiment.py` to validate the experiment module loads.
- `psynet test local` with `Exp.test_n_bots = 10` to exercise the bot path and automated assertions.
- `psynet simulate` to produce `evidence/simulated_data.zip` for analysis.
- An executed canonical notebook at `evidence/analyses/analysis.ipynb` reading the exported CSVs directly and showing:
  - the reported participant profile distribution from completed simulated participants (`random` count and `normal_rgb` count);
  - a profile stability table by participant;
  - response validity checks for integer range `[0, 255]`;
  - a lightweight behavioral comparison, such as random-profile response range/variance versus normal-profile response distance from the starting active-channel value.
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output <attempt>/evidence/performance.json` unless blocked by the local environment, in which case the blocker will be recorded in `EVALUATION.md`.

Evidence deliverables will include `evidence/profile_distribution.*` or an equivalent notebook/report section that explicitly shows the observed counts came from completed simulated participants. `REPORT.md` will summarize how the original Gibbs task was preserved, how profiles were assigned, what the reported distribution was, and what limitations remain.

## Human review questions

Please review this plan before implementation, as required by the experiment implementation workflow. Two details are especially worth confirming:

1. Should the normal profile use a fixed standard deviation such as 20 RGB units, or would you prefer a different value?
2. Which GitHub username should be credited in `agent.json` for this attempt? Current known author keys are listed in `authors.yaml`; the field is temporarily left empty during this review pause.
