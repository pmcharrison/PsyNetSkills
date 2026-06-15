# Learnings

## Ordered static lobby trials need explicit blocks

PsyNet `StaticTrialMaker` can balance or randomize node allocation unless the
visible sequence is encoded explicitly. For a lobby where "10 personality
iterations, then 30 guessing iterations" matters, one ordered block per node plus
`choose_block_order` makes the participant-facing order testable.

*Actions:*

- **PsyNetSkills:** Add a short note to the simple-round-structure skill that `StaticTrialMaker` default allocation is not enough when visible trial order matters; use explicit blocks and `choose_block_order`. Confidence: high. Impact: medium. Status: considering.

## Playwright videos need Playwright's ffmpeg binary

System `ffmpeg` is not sufficient for Playwright's built-in `recordVideo`
feature. The first participant-flow run failed until `npx playwright install
ffmpeg` installed Playwright's own binary.

*Actions:*

- **PsyNetSkills:** Keep the record-participant-video guidance that calls out `npx playwright install ffmpeg` before using Playwright `recordVideo`; this attempt reconfirmed the failure mode. Confidence: high. Impact: medium. Status: completed.
