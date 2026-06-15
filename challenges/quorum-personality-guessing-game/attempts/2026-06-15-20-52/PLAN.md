# Plan

## Methods

Participants will complete a synchronous PsyNet experiment with a productive quorum lobby followed by the quorum tutorial's quorate main loop. The quorum will use groups of three participants. Participants who arrive before a quorate group is available will complete a two-stage personality and guessing-game lobby task rather than seeing an idle waiting page. When at least three active participants are present in the same group, PsyNet will release them from the lobby into the main loop together.

The lobby will offer up to 40 productive waiting iterations. The first stage will contain 10 personality iterations using the ten short Big Five items from `references/personality-items.md`, formatted with the stem "I see myself as someone who ...". Each personality item will use a five-option accuracy scale: "Very inaccurate", "Moderately inaccurate", "Neither accurate nor inaccurate", "Moderately accurate", and "Very accurate". Each saved response will identify the participant, task type, item id, key, facet, prompt text, and selected accuracy response.

The second lobby stage will contain 30 guessing-game iterations. Each guessing iteration will define a hidden integer target from 0 to 10 inclusive. Participants will choose an integer guess from 0 to 10 with a PsyNet `SliderControl`. The target will not appear on the response page. After submission, participants will see feedback derived from the absolute difference between guess and target: exact target gives a success message, difference 1 gives "Warmer", difference 2 gives "A little warmer", and larger differences give "Cold". Saved data will include participant id, task type, iteration number, node id, target, guess, absolute difference, and feedback label.

The lobby pages will make clear that participants need not finish all 40 waiting iterations. If the quorum is obtained, PsyNet may release them into the main loop as soon as the synchronization condition is met. All participant-facing pages will state the task phase and current iteration. Time estimates and limits will be set for instructions, personality responses, guesses, feedback, and group waits so that one inactive participant cannot block the group indefinitely. If quorum is lost after release, the experiment will use PsyNet synchronization checks to send remaining participants back into productive waiting trials when top-up is possible; otherwise it will show a clear unsuccessful-end message that explains why the synchronous session cannot continue.

## Implementation

The experiment will be implemented as a self-contained PsyNet experiment under `code/quorum_personality_guessing_game/`, rather than directly in `code/`, to avoid colliding with Python's standard-library `code` module. I will start from the current `sync_quorum` demo support-file layout, including `.gitignore`, `config.txt`, `test.py`, and standard Docker/helper files where they are needed by PsyNet local launch checks.

The core timeline will use PsyNet's native synchronization tools:

- `SimpleGrouper(group_type="quorum", initial_group_size=3, min_group_size=3, max_group_size=None, join_existing_groups=True, waiting_logic=..., waiting_logic_expected_repetitions=..., max_wait_time=...)` adapted from the quorum tutorial.
- A task-specific `join_criterion` that allows late/top-up participants to join only active, incomplete quorum groups whose main loop is still in a joinable state.
- `trial_maker.custom(...)` around the grouper and tutorial-style main-loop logic so waiting participants receive two-stage lobby trials while the quorum forms.
- Explicit `conditional` checks before each main iteration to verify `participant.sync_group.n_active_participants >= participant.sync_group.min_group_size`.
- `GroupBarrier` checkpoints where needed to keep grouped participants aligned before entering the main loop and between main iterations.
- `GroupCloser(group_type="quorum")` near the end so completed groups are closed cleanly.

The waiting task will be a separate `StaticTrialMaker` with its own id, for example `lobby_tasks`. Its node list will contain the 10 personality nodes followed by 30 guessing nodes. Its trial class will branch on `self.definition["task_type"]`: personality pages will use `PushButtonControl`, and guessing pages will use `SliderControl(start_value=5, min_value=0, max_value=10, n_steps=11)` followed by server-side feedback. The trial maker will allow repeated nodes if a participant waits longer than 40 pages, and saved metadata will tag all responses as lobby data so they remain analytically separate from the quorate main loop.

The post-quorum main loop will keep the quorum demo's structure: a `for_loop` labeled as the quorate phase, repeated explicit quorum checks, and quorate status pages that report how many other participants are present. The personality and guessing tasks will not be delivered through this main loop.

Bot behavior will cover normal and edge paths. Serial bots will start below quorum to assert that participants receive lobby personality trials and lobby guessing trials before release, then add enough bots to release a quorate group into the tutorial-style main loop before the lobby sequence is necessarily complete. Bot responses will choose deterministic personality labels and guessing values that exercise exact, difference-1, difference-2, and cold feedback. A dropout/top-up scenario will fail one active participant after quorum release, assert the remaining participants return to waiting or receive the intended clear end-state, then add a replacement bot when the join criterion permits it.

## Validation and evidence

After human approval of this plan, implementation will be validated from the experiment directory with:

- `python experiment.py`
- `psynet test local`
- `psynet simulate`, saving `evidence/simulated_data.zip`
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output <attempt>/evidence/performance.json`

I will inspect exported CSVs to confirm lobby responses and main-loop responses are separable and contain the requested fields. I will create `evidence/analyses/analysis.ipynb` that reads the simulated export directly, summarizes lobby personality responses, verifies lobby guessing feedback categories, and checks participant/group coverage. I will also collect participant-flow evidence with the `record-participant-video` workflow, including a short recording and targeted screenshots that show personality lobby trials, guessing lobby trials, quorum release before the lobby sequence is finished, quorate main-loop pages, and group-loss/top-up behavior. A final `REPORT.md` will summarize implementation, simulation, analysis, validation, and limitations.

## Human review questions

- Is a quorum size of three acceptable for this challenge attempt?
- Should the lobby guessing targets be deterministic across participants for easier evidence review, or independently generated for each participant's waiting trials?
- Should stranded participants be returned to productive waiting whenever top-up is possible, or should the main session end immediately after group loss?
