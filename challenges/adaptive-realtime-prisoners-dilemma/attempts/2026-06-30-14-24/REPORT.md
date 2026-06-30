# Report

## Implementation

The attempt implements a PsyNet experiment in
`code/adaptive_realtime_prisoners_dilemma/`.

Key features:

- Dyads are formed with `SimpleGrouper(group_type="pd_dyad")`.
- Treatment assignment is owned by the trial maker's network allocation:
  treatment is a fixed node/network definition, and `prioritize_networks` orders
  candidate treatment networks using either static balancing or adaptive scoring.
  The adaptive decision audit record is copied into the selected trial
  definition/answer, not written into all candidate network vars.
- Each dyad plays the 10-iteration game within one custom PsyNet `Page`, so the
  participant-facing sequence proceeds without page reloads.
- The live game HTML and JavaScript live in
  `templates/live_pd_sequence.html`, keeping `experiment.py` focused on PsyNet
  state, treatment allocation, and template arguments.
- The live game page uses a dedicated websocket channel for choices, results,
  state snapshots, and chat messages.
- The live game page requests a server-owned state snapshot on load, so a browser
  refresh can restore completed rounds, current round, bonus total, and whether the
  participant already submitted the current choice.
- Websocket choice handling stores live operational state in a dedicated
  `PDLiveSession` table, locks the dyad's session row before mutation, rejects
  stale or duplicate choices, and broadcasts results/chat messages to explicit
  dyad recipient ids. Chat messages are persisted in the same session row and
  restored from state snapshots after browser refresh.
- Session state is updated by the `PDLiveSession.reduce_event(event, participants)`
  method, which accepts a persisted `PDLiveEvent` object and mutates the locked
  session row. Treatment is stored with the other session parameters in
  `PDLiveSession.state`, and choice/chat events share the same reducer interface;
  event-type branching is kept inside the experiment-specific session reducer
  implementation.
- The participant-facing game interface avoids exposing treatment labels,
  participant IDs, and internal points; it presents bonuses in dollars and
  updates PsyNet's footer reward display as the game progresses.
- Instructions are shown inside the allocated trial after dyad formation and
  treatment assignment, so communication is mentioned only for dyads in the
  communication treatment.
- The dyad grouper uses explicit dyad batching and a 180-second wait window for
  manual review sessions.
- The finalized `trial.answer` contains the full ordered action sequence for
  both players, final-round mutual-cooperation event, treatment, bonus, and
  assignment metadata.
- Adaptive scoring uses the analytical Beta-Bernoulli active-inference EIG
  expression with a gamma-scaled expected utility term over posterior probability of
  final-round `(Cooperate, Cooperate)`.
- The adaptive utility scale is `GAMMA = 0.1`.
- Treatment optimization is encapsulated in
  `ActiveInferenceTreatmentOptimizer`, so future attempts can swap in another
  optimizer without changing the trial-maker allocation interface.

## Validation

Passed:

- `python -m py_compile experiment.py adaptive_logic.py simulate_procedure.py`
- `python experiment.py`
- `python simulate_procedure.py`
- `psynet test local`
- `psynet simulate`
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output .../evidence/performance.json`

The local PsyNet bot test verifies that a dyad reaches the single live game page,
submits a 10-round sequence answer, finalizes a `trial.answer` with all 10 rounds,
and records adaptive assignment metadata. The bot test now runs four bots as two
dyads and verifies that each finalized sequence contains only the two
participants belonging to that dyad.

## Simulation and analysis

`evidence/simulated_data.zip` contains:

- A PsyNet `psynet simulate` export under `psynet_export/`.
- An offline dyad-level active-inference simulation under `offline/`.

`evidence/analyses/analysis.ipynb` reads the simulated export ZIP and summarizes
treatment assignment, final-round mutual cooperation, and the evolution of EIG,
expected utility, and negative expected free energy (`-G`) for each treatment.
It also plots the cumulative number of times each treatment was delivered.
The notebook uses `matplotlib`; the analysis dependency is recorded in
`evidence/analyses/requirements.txt`.

## Blockers and limitations

- `dallinger constraints generate` failed repeatedly because PyPI requests were
  reset by the network. A documented minimal `constraints.txt` is included so
  local PsyNet checks can proceed, but maintainers should regenerate it when
  network access is stable.
- `scipy` is declared in `requirements.txt` and expected for deployment. Local
  installation failed repeatedly due PyPI connection resets, so `adaptive_logic.py`
  includes an exact positive-integer digamma fallback for this Beta-Bernoulli
  model. The intended production path remains `scipy.special.digamma`.
- `psynet debug local` could not be used for GUI recording because the missing
  SciPy dependency is enforced by debug prechecks.
- The performance test completed and wrote `evidence/performance.json`, but
  SciPy remains unavailable in the local venv. The implementation therefore uses
  the exact positive-integer digamma fallback during local tests.

## Review notes

The most important remaining review item is a browser-based two-participant
recording once SciPy can be installed and `psynet debug local` can launch. That
recording should verify that the custom JavaScript page advances all 10 rounds
without reloads, websocket result broadcasts update both participants, and chat
appears only in the communication treatment.
