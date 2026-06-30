# Plan

## Science

This experiment estimates whether real-time communication increases mutual
cooperation in a 10-iteration Prisoner's Dilemma. The adaptive policy treats each
dyad as one assignment unit. The primary outcome `y` will be whether both players
cooperate in the final round: `1` for `(Cooperate, Cooperate)` in round 10, and
`0` otherwise. The adaptive objective is to assign future dyads to the treatment
with the highest predicted probability of final-round mutual cooperation while
retaining enough stochastic exploration to learn from both treatments.

The two treatments are:

1. **No communication.** Dyad members play the full sequence without chat.
2. **Communication.** Dyad members can chat during the real-time game.

The adaptive unit is the dyad-level treatment. The main covariate set `z` will be
empty in the first implementation, apart from exported metadata such as dyad id,
sequence number, experiment mode, and random seed. This keeps the first adaptive
model auditable and aligned with the challenge objective.

## Methods

Participants will read instructions explaining the two actions, the payoff
consequences, the simultaneous nature of play, the chat condition, timers, sound
cues, and bonus conversion. They will then enter a waiting room until PsyNet can
form a dyad. Grouping will use a `SimpleGrouper` with `initial_group_size=2`,
explicit wait limits, and participant-facing waiting text. A `GroupBarrier` will
release the two participants together and atomically assign stable roles, a dyad
id, the experiment mode, and the dyad treatment.

Each dyad will play one 10-iteration game. In each iteration both participants
will receive an audible cue and a visible countdown, then choose between two
globally configurable actions rendered as **Play "Cooperate"** and
**Play "Defect"** by default. The payoff explanation will use an explicit,  
participant-centered table that is straightforward to read. Rows will be labelled  
with the participant's possible choices, for example **If I play Cooperate** and
**If I play Defect**. Columns will be labelled with the partner's possible
choices, for example **If my partner plays Cooperate** and **If my partner plays
Defect**. Each cell will state the participant's own reward in direct language,
for example **I get $0.12**, rather than using abstract payoff notation. A short
caption will explain that the partner sees the same table from their own
perspective. The exact payoff values and point-to-bonus exchange rate will be
defined as global constants and shown in the instructions and during play.

Participants will submit choices simultaneously. The server will reject duplicate
or stale submissions, enforce deadlines, compute payoffs after both choices or
timeouts are resolved, and broadcast a filtered feedback snapshot to both
participants. Feedback will show each player's action, each player's iteration
points, cumulative points, estimated bonus, and the next iteration timer. After
10 iterations, participants will see a final summary and bonus amount.

In the communication treatment, a chat panel will appear to the right of the game
area and remain available during the sequence. In the no-communication treatment,
the chat panel will be absent and the game layout will use the available space
without implying that chat is broken or hidden. Chat will never determine phase
advancement or scoring.

## Implementation

The attempt will live in
`challenges/adaptive-realtime-prisoners-dilemma/attempts/2026-06-30-14-24/code/adaptive_realtime_prisoners_dilemma/`.
The implementation will start from the current PsyNet `rock_paper_scissors`
demo for dyadic grouping, synced trial allocation, barriers, chatroom usage, and
serial bot tests. It will also inspect `simple_sync_group`, `create_rate_sync`,
`sync_quorum`, `gibbs_within_sync`, the chatroom docs/demo, and the
`WebSocketElt` framework API before coding.

The planned PsyNet structure is:

- `EXPERIMENT_MODE = "adaptive"` or `"static"` as the central global mode switch
in `experiment.py`.
- Global constants for action labels, payoff matrix, sequence length, response
deadline, cue settings, treatment names, static assignment rule, and
point-to-bonus exchange rate.
- `EnableChatrooms()` at the start of the timeline for the communication
treatment.
- `SimpleGrouper(group_type="pd_dyad", initial_group_size=2, max_wait_time=...)`
to form dyads.
- A `GroupBarrier(on_release=...)` after grouping to sort participants by id,
assign roles, assign treatment, and persist a dyad-assignment record.
- One synchronized static trial allocated with `sync_group_type="pd_dyad"` whose
node parameters define the treatment, payoff matrix, action labels, deadlines,
and sequence length.
- A custom live game page backed by a custom `WebSocketElt` channel for
real-time choices, timers, state snapshots, feedback, page reload recovery, and
participant-specific visibility.
- PsyNet `ChatRoom` for communication dyads only, with the room id derived from
the trial maker's sync-group namespace, e.g.
`sync_group = participant.active_sync_groups[self.trial_maker.sync_group_type]`
followed by a room id based on `sync_group.id`, rather than relying directly on
`participant.sync_group`.
- `GroupCloser(group_type="pd_dyad")` after the sequence to prevent accidental
reuse of completed groups.

The server will own the live game session state. Browser JavaScript will render
state, play the audible cue after a user gesture has enabled audio, display
countdowns, and send choice/chat messages, but it will not decide phase
advancement, scoring, or treatment assignment. The live-session layer will store
raw submitted events, server checkpoint state, and outbound participant-specific
snapshots separately enough to audit websocket synchronization.

At the end of the 10-iteration sequence, the finalized PsyNet `trial.answer`
will contain the full ordered sequence of actions for both players. This answer
will include one entry per iteration with each participant's role or id, each
submitted action, submission timing or timeout status, payoffs, cumulative
scores, and the treatment. Summary outcome records may duplicate these values
for analysis, but they will not replace the sequence-level `trial.answer`.

Adaptive logic will be isolated in `adaptive_logic.py`. The first implementation
will use a Beta-Bernoulli two-arm model with one arm per treatment. For each
completed dyad, the model observes `successes = 1` if both players cooperated in
round 10 and `successes = 0` otherwise, with `trials = 1`. Posterior state will
be recomputed from all finalized dyad last-round mutual-cooperation outcomes
before each assignment (`from_scratch` strategy) to avoid stale online updates
under concurrent recruitment. The adaptive choice rule will use active
inference, not a fallback bandit policy: each candidate treatment will be scored
by expected information gain plus an expected-utility term. The utility will be
the posterior predictive probability of final-round mutual cooperation, and the
utility contribution will be scaled by a global
`GAMMA` parameter. The exact expected information gain formula should follow the
active-inference reference paper/code before implementation, and the
implementation should keep the EIG term, expected utility term, `GAMMA`, and
combined score inspectable in exported assignment records.

Adaptive assignment records will include experiment mode, dyad id, candidate
treatments, selected treatment, posterior parameters, predictive cooperation
probabilities, decision score components, data cutoff, random seed, algorithm
version, and decision timing. Dyad outcome records will include raw choices,
cooperation counts, payoffs, final bonuses, timeout flags, and chat availability.

Bots and simulations will be designed before final validation. Bot profiles will
include at least cooperative, defecting, and mixed strategies so static and
adaptive paths produce analyzable variation. The bot path will exercise both
treatments and both experiment modes through the same response schema used by
browser participants.

## Validation and evidence plan

Functional checks will run from the experiment directory:

- `python experiment.py`
- `psynet test local`

The first local bot tests will use `test_n_bots >= 4` so at least two dyads can
form, one in each static treatment. Adaptive tests will use a fixed random seed
and enough bot dyads to prove that posterior parameters update from observed
cooperation outcomes and influence later assignments. Serial tests will use
`advance_past_wait_pages`; a parallel or multi-browser test will be added for
websocket routing and concurrent arrival behavior.

The evidence package will include:

- `evidence/participant.mp4` showing two participants grouped, released, playing
10 iterations, hearing/seeing timer cues, receiving feedback, and completing
with bonuses.
- `evidence/screenshots/` for no-communication layout, communication layout,
feedback state, final bonus page, and adaptive metadata if visible in local
review tooling.
- `evidence/performance.json` from `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0`.
- `evidence/monitor.html` with a dashboard monitor snapshot.
- `evidence/simulated_data.zip` from `psynet simulate`.
- `evidence/analyses/analysis.ipynb`, executed in place, reading exported CSVs
directly and summarizing treatment assignment, cooperation rates, chat
availability, payoffs, and adaptive posterior history.
- `REPORT.md` summarizing implementation, validation, simulation, analysis, and
limitations.

## Review questions before coding

- Confirm the human author GitHub key for `agent.json`.
- Confirm that the default action labels should be **Cooperate** and **Defect**,
while remaining globally configurable.
- Confirm the active-inference scoring formula after inspecting the reference
paper/code, including the exact EIG expression and the default `GAMMA` value.

