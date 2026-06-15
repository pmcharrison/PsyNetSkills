# Plan

## Methods

Participants will first see instructions explaining that the experiment has a
quorum-gated main phase and that they may be advanced from the lobby as soon as
enough active participants are present. The instructions will also describe the
two productive waiting tasks, how personality and guessing responses are
recorded, the hidden target in the guessing task, and the intended behavior when
a participant times out or the group falls below quorum.

The lobby will contain a fixed menu of 40 possible waiting trials. The first 10
trials will present the short Big Five items supplied in
`references/personality-items.md`. Each prompt will use the style "I see myself
as someone who ..." and will collect a five-point accuracy response from "Very
inaccurate" to "Very accurate". The next 30 trials will present a guessing game.
Each guessing trial will assign a hidden target integer from 0 to 10 inclusive,
ask the participant to guess with a 0-10 slider, and then show feedback based on
the absolute difference: exact success, "Warmer" for a difference of 1, "A
little warmer" for a difference of 2, and "Cold" for larger differences.

The 40 lobby trials will not be a completion requirement. They will serve as
waiting content while PsyNet's synchronization barrier forms or repairs the
quorum. If the group becomes quorate while a participant is still in the lobby,
PsyNet may release that participant into the main phase before all lobby trials
have been completed.

Once released, participants will enter the quorum tutorial's main loop rather
than another personality or guessing block. The loop will run repeated quorate
status iterations while the group remains above the minimum active group size.
If the group falls below quorum, remaining active participants will either
return to productive waiting through the same lobby waiting logic or reach a
clear unsuccessful/end state if synchronization cannot recover within the
configured wait limits.

## Implementation

The runnable experiment will live under `code/quorum_personality_guessing_game/`
so that PsyNet imports the experiment package without colliding with Python's
standard-library `code` module. The implementation will adapt the current
`sync_quorum` demo from `~/PsyNet/demos/experiments/sync_quorum/experiment.py`.
The core timeline shape will be:

1. `InfoPage` for the quorum, lobby-task, recording, timeout, and completion
   instructions.
2. A lobby `StaticTrialMaker` with 40 ordered `StaticNode`s.
3. `lobby_trial_maker.custom(SimpleGrouper(...), post_quorum_loop)` where the
   grouper uses `initial_group_size=3`, `min_group_size=3`,
   `join_existing_groups=True`, `waiting_logic=PageMaker(lobby_trial_maker.cue_trial)`,
   `waiting_logic_expected_repetitions=40`, and an explicit `max_wait_time`.
4. A post-quorum `for_loop` with a `conditional("check_quorate", ...)` that
   sends quorate participants to tutorial-style status pages and under-quorate
   participants back through the lobby waiting logic.
5. A final completion `InfoPage` summarizing that the quorate main loop was
   completed, without implying that unfinished lobby pages were mandatory.

The lobby trial maker will use a single `LobbyTrial` subclass of `StaticTrial`
that branches on `definition["task_type"]`. Personality nodes will store
`task_type`, `lobby_index`, `item_id`, `item_key`, `facet`, and `item_text`, and
will render a `ModularPage` with `PushButtonControl`. Guessing nodes will store
`task_type`, `lobby_index`, `round_id`, and `target`, and will render a
`ModularPage` with `SliderControl(start_value=5, min_value=0, max_value=10,
snap_values=11)`. The target will stay out of the pre-submit prompt.

Guessing responses will be normalized to integers before scoring. The saved
trial data will include the target, guess, absolute difference, feedback label,
lobby index, task type, node identifier where available, and participant
identifier where available from the exported trial record. Lobby data will
remain analytically separate from main-loop data by keeping all personality and
guessing pages inside the lobby trial maker and keeping the quorate status pages
outside it.

The experiment will define bot behavior and tests before final evidence
collection. The serial bot test will cover pre-quorum lobby work, release into
the quorate loop only after three active participants are present, return to
lobby work after simulated group loss, and top-up behavior through
`join_existing_groups=True`. Unit-style assertions around trial definitions and
feedback scoring will cover all required feedback labels, including exact
guesses and differences of 1, 2, and greater than 2.

## Validation and evidence plan

After implementation, validation will run from the experiment directory with:

- `python experiment.py`
- `psynet test local`
- `psynet simulate` with enough bots to exercise quorum formation, lobby data,
  main-loop data, and recovery paths, saving `evidence/simulated_data.zip`
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0`
  with JSON output saved under `evidence/performance.json`

Participant-facing evidence will be collected with the repository's
`record-participant-video` workflow. The evidence should show at least one
participant completing lobby personality and guessing pages before quorum,
multiple participants being released into the main quorate loop only when the
quorum exists, and the visible recovery or end-state behavior after a simulated
participant failure. The analysis notebook will read the simulated export
directly and summarize lobby personality responses, guessing feedback
distribution, quorum/main-loop records, and recovery/failure markers.

## Open review questions

- Which GitHub username should be credited in `agent.json` as the human author of
  this attempt?
- Is a quorum size of three acceptable, matching the current PsyNet tutorial
  demo, or should the implementation use a different minimum group size while
  preserving the same native PsyNet synchronization pattern?
- Should the guessing targets be deterministic for reproducible evidence, or
  pseudo-random with a fixed seed recorded in the report?

Implementation is intentionally paused here for human plan review, as required
by the experiment implementation workflow.
