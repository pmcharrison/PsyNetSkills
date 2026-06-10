# Participant flow test summary

The PsyNet participant flow launches and the Unity WebGL build loads successfully.
A GUI-driven participant run completed all three Unity trials after the runner
strategy was adjusted to use rapid `ArrowUp` bursts with occasional side-key
corrections and no `ArrowDown`.

## Successful checks

- Unity assets were served by the local PsyNet server after `static/scripts/` was
  allowed into PsyNet's source package.
- Unity initialized in Chrome and logged `Init` / `GetPage` messages.
- The experiment uses a `StaticTrialMaker` with `max_trials_per_participant=3`.
- The successful GUI run completed three Unity trials, selecting ferries and
  submitting ratings each time.
- The run reached the PsyNet task-complete page and the final 100% completion
  page with a `Finish` button.

## Evidence files

- `ferry_market_unity_success_slideshow.mp4`: screenshot slideshow of the
  successful run. This is not a continuous screen recording; the screen recorder
  failed to save the full live recording.
- `screenshots/`: key screenshots from landing, consent, instructions, Unity
  trials, ferry/rating screens, task completion, and final Finish page.
- `participant-actions-*.json`: earlier headless Playwright attempts showing
  Unity load and browser input experiments before the GUI strategy succeeded.

## Notes

The successful GUI strategy used rapid `ArrowUp` bursts with minimal pauses and
occasional `ArrowLeft`/`ArrowRight` corrections. Slow or held-key approaches were
not sufficient in earlier automated attempts.
