# Evidence workflow demo

This static browser fixture demonstrates the preferred evidence workflow for participant-facing review artifacts.

Run the Playwright flow from this directory:

```bash
npm install
npm test
```

The test asserts participant behavior and writes screenshots to `../../evidence/screenshots/`.
For recording, run the same test headed at a readable pace while `ffmpeg`
captures the browser display:

```bash
PARTICIPANT_FLOW_SCREENSHOTS=0 PARTICIPANT_FLOW_STEP_MS=450 npm run test:headed
```
