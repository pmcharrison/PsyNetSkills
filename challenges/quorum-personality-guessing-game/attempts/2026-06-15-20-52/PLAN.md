# Plan

## Methods

Participants will complete a synchronous PsyNet experiment with a productive quorum lobby followed by a 40-iteration main task. The quorum will use groups of three participants. Participants who arrive before a quorate group is available will answer short personality-style filler questions rather than seeing an idle waiting page. When at least three active participants are present in the same group, PsyNet will release them into the main loop together.

The main loop will contain 10 personality iterations followed by 30 guessing-game iterations. The personality iterations will use the ten short Big Five items from `references/personality-items.md`, formatted with the stem "I see myself as someone who ...". Each personality item will use a five-option accuracy scale: "Very inaccurate", "Moderately inaccurate", "Neither accurate nor inaccurate", "Moderately accurate", and "Very accurate". Each saved response will identify the participant, task type, item id, key, facet, prompt text, and selected accuracy response.

The guessing-game iterations will each define a hidden integer target from 0 to 10 inclusive. Participants will choose an integer guess from 0 to 10 with a PsyNet `SliderControl`. The target will not appear on the response page. After submission, participants will see feedback derived from the absolute difference between guess and target: exact target gives a success message, difference 1 gives "Warmer", difference 2 gives "A little warmer", and larger differences give "Cold". Saved data will include participant id, task type, iteration number, node id, target, guess, absolute difference, and feedback label.

All participant-facing pages will state the task phase and current iteration. Time estimates and limits will be set for instructions, personality responses, guesses, feedback, and group waits so that one inactive participant cannot block the group indefinitely. If quorum is lost after release, the experiment will use PsyNet synchronization checks to send remaining participants back into productive waiting trials when top-up is possible; otherwise it will show a clear unsuccessful-end message that explains why the synchronous session cannot continue.

## Implementation

The experiment will be implemented as a self-contained PsyNet experiment under `code/quorum_personality_guessing_game/`, rather than directly in `code/`, to avoid colliding with Python's standard-library `code` module. I will start from the current `sync_quorum` demo support-file layout, including `.gitignore`, `config.txt`, `test.py`, and standard Docker/helper files where they are needed by PsyNet local launch checks.

The core timeline will use PsyNet's native synchronization tools:

- `SimpleGrouper(group_type="quorum", initial_group_size=3, min_group_size=3, max_group_size=None, join_existing_groups=True, waiting_logic=..., waiting_logic_expected_repetitions=..., max_wait_time=...)` adapted from the quorum tutorial.
- A task-specific `join_criterion` that allows late/top-up participants to join only active, incomplete quorum groups whose main loop still has enough remaining work.
- `trial_maker.custom(...)` around the grouper and main-loop logic so waiting participants receive filler trials while the quorum forms.
- Explicit `conditional` checks before each main iteration to verify `participant.sync_group.n_active_participants >= participant.sync_group.min_group_size`.
- `GroupBarrier` checkpoints where needed to keep grouped participants aligned before entering the main loop and between main iterations.
- `GroupCloser(group_type="quorum")` near the end so completed groups are closed cleanly.

The waiting filler task will be a separate `StaticTrialMaker` with its own id, for example `waiting_personality`. Its trial class will present personality-style prompts with `PushButtonControl`, use the same five accuracy labels, allow repeated nodes, and tag saved metadata with `task_type="waiting_personality"` so waiting responses are analytically separate from the 40 main iterations.

The main task will be a synchronized `StaticTrialMaker` with `sync_group_type="quorum"`, `expected_trials_per_participant=40`, and `max_trials_per_participant=40`. Its node list will contain:

- 10 `StaticNode`s for personality items, each with `task_type="personality"`, `iteration`, `item_id`, `key`, `facet`, and item text.
- 30 `StaticNode`s for guessing iterations, each with `task_type="guessing"`, `iteration`, `guessing_round`, and a pre-generated hidden target between 0 and 10.

The main trial class will branch on `self.definition["task_type"]`. Personality pages will render a `ModularPage` using `PushButtonControl` and save the chosen accuracy response. Guessing pages will render a `ModularPage` using `SliderControl(start_value=5, min_value=0, max_value=10, n_steps=11)` and will not display the target. Guessing feedback will be computed server-side after the answer is received, saved on the trial with `self.var` fields, and displayed on a separate feedback page.

Bot behavior will cover normal and edge paths. Serial bots will start below quorum to assert that participants receive waiting personality trials first, then add enough bots to release a quorate group into the main loop. Bot responses will choose deterministic personality labels and guessing values that exercise exact, difference-1, difference-2, and cold feedback. A dropout/top-up scenario will fail one active participant after quorum release, assert the remaining participants return to waiting or receive the intended clear end-state, then add a replacement bot when the join criterion permits it.

## Validation and evidence

After human approval of this plan, implementation will be validated from the experiment directory with:

- `python experiment.py`
- `psynet test local`
- `psynet simulate`, saving `evidence/simulated_data.zip`
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output <attempt>/evidence/performance.json`

I will inspect exported CSVs to confirm main and waiting responses are separable and contain the requested fields. I will create `evidence/analyses/analysis.ipynb` that reads the simulated export directly, summarizes personality responses, verifies guessing feedback categories, and checks participant/group coverage. I will also collect participant-flow evidence with the `record-participant-video` workflow, including a short recording and targeted screenshots that show waiting trials, quorum release, personality trials, guessing trials before and after feedback, and group-loss/top-up behavior. A final `REPORT.md` will summarize implementation, simulation, analysis, validation, and limitations.

## Human review questions

- Is a quorum size of three acceptable for this challenge attempt?
- Should the hidden guessing targets be shared by all group members on a synchronized node, or should each participant have an independent target while remaining synchronized by iteration?
- Should stranded participants be returned to productive waiting whenever top-up is possible, or should the main session end immediately after group loss?
