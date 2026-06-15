# Report

## Implementation summary

The attempt implements a self-contained PsyNet experiment in
`code/quorum_personality_guessing_game/`. The experiment adapts PsyNet's
`sync_quorum` tutorial pattern with a native `SimpleGrouper`, `waiting_logic`,
`join_existing_groups=True`, a minimum quorum size of three, and explicit
quorate checks before the main loop.

The waiting-room task is a 40-node ordered `StaticTrialMaker`. The first 10
nodes are the supplied short Big Five personality items, rendered with
`PushButtonControl` and a five-point accuracy scale. The next 30 nodes are
guessing-game trials rendered with `SliderControl` from 0 to 10. Guessing targets
are hidden before submission and stored with the submitted guess, absolute
difference, and feedback label.

The post-quorum main phase remains a tutorial-style quorate status loop. If the
group falls below quorum during the loop, the conditional branch sends remaining
participants back into the same productive waiting logic while top-up
participants can join through the native grouper behavior.

## Validation

- `python experiment.py` passed as an import/run sanity check.
- `psynet test local` passed after iterating on ordered lobby blocks and the
  serial bot scenario.
- The final serial bot scenario covers pre-quorum personality and guessing
  lobby trials, exact/difference-1/difference-2/greater-than-2 feedback labels,
  release only after quorum, simulated participant failure, and top-up recovery.
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0`
  completed with zero bot errors and zero request errors.

## Evidence

- `evidence/participant.mp4` records a participant reading instructions,
  completing personality lobby pages, reaching a hidden-target guessing slider,
  receiving feedback, and entering the quorate main loop.
- `evidence/screenshots/` contains targeted screenshots for instructions,
  personality push buttons, hidden-target guessing, guessing feedback, and
  quorate release.
- `evidence/simulated_data.zip` contains a `psynet simulate` export with
  personality trials, guessing trials, synchronization records, and a simulated
  failure/recovery scenario.
- `evidence/analyses/analysis.ipynb` reads the simulated export directly and
  summarizes lobby coverage, personality metadata, guessing feedback, participant
  outcomes, and synchronization records.
- `evidence/performance.json` and `evidence/performance-test.log` contain the
  sustained load-test evidence.
- `evidence/monitor.html` is an authenticated local dashboard monitor snapshot
  captured from the debug deployment.

## Findings and limitations

The evidence confirms that lobby data is analytically separate from quorate
main-loop pages, and that the guessing feedback categories are saved in the
export. The visual recording is intentionally concise; it demonstrates the
participant-facing happy path and quorate release, while the automated bot test
and simulated export cover failure/recovery behavior.
