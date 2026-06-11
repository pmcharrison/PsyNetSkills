# Evidence

This example evidence was generated from `code/evidence-workflow-demo/tests/participant-flow.spec.js`.

- `screenshots/` came from the normal headless Playwright assertion run.
- `participant.mp4` came from the same Playwright test run headed at a readable
  pace with `PARTICIPANT_FLOW_SCREENSHOTS=0` while `ffmpeg` recorded the display.

The same committed Playwright flow therefore asserts behavior, captures review
screenshots, and drives the participant recording.
