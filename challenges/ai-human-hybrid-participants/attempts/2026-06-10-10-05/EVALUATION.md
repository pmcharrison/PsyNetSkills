---
score: 8
feedback: |
  Better than the first attempt because it allows active scheduling.
  Weaknesses: there is no safeguard for parallel AI running overload; the active
  scheduling algorithm should expose a customizable hard cap for concurrently
  running AI participants, defaulting to a hard limit such as 40, and should use
  successful and currently-running bot counts to control launches. Testing lacks
  a standard procedure for actually testing the experiment with human
  participants under different AI proportions. For future attempts, if there are
  instruction pages for human participants, their content should also be
  integrated into the AI participants' system prompt.
---

# Evaluation

## Summary

Human evaluator score: 8/10. The attempt is better than the first attempt because
it implements active scheduling, but it still needs an explicit parallel-AI
overload safeguard and a clearer standard procedure for human testing across AI
proportions.

## Strengths

- Better than the first attempt.
- Allows active scheduling for hybrid human-AI participation.

## Weaknesses

- No safeguard limits parallel AI overload; the scheduler should expose a
  customizable hard cap for concurrently running AI participants, with a hard
  default such as 40.
- The scheduler should consider successful bots and currently running bots when
  deciding whether to launch more AI participants.
- Testing lacks a standard procedure for exercising the experiment with human
  participants under different AI proportions.
- Future implementations should integrate human participant instruction-page
  content into the AI participants' system prompt.

## Criteria

- [x] The attempt starts from the PsyNet Gibbs sampling demo and preserves the
  original pure-human behavior when the AI participant proportion is `0`.
- [x] AI proportion configuration accepts the full `0` to `100` range, rejects
  invalid values, and is documented together with required OpenRouter settings.
- [x] The implementation contains a `bot_response` path that uses the same
  stimulus values shown to human participants, calls OpenRouter through
  configurable credentials, parses the model response, and submits data in the
  original experiment response format.
- [x] The AI prompt closely matches the human-facing instructions, specifies the
  required output format, and does not reveal extra information unavailable to
  human participants.
- [x] Human and AI trial presentation are kept consistent by deriving both the
  human display and AI prompt from the same trial data rather than maintaining
  divergent stimulus definitions.
- [x] The scheduling or assignment logic launches AI participants in a way that
  tracks the configured target proportion across mixed human-AI sessions.
- [ ] Tests or executable checks cover pure-human, mixed, and all-AI settings,
  configuration validation, prompt/stimulus consistency, scheduler behavior,
  and OpenRouter calls using mocks or environment-supplied credentials.
- [x] The solution avoids committing real API keys, production credentials, or
  unrelated changes to the shared PsyNet checkout.

## Notes

- Score and feedback should come from a human evaluator, captured
  conversationally when working with Cursor Cloud Agents.
- Evidence collected: `participant.mp4`, `performance.json`, `monitor.html`,
  `data.zip`, `participant-ffprobe.log`, and `ai-bot-run.log`.
- No real OpenRouter credential was used or committed. The AI path was tested
  with the local deterministic mock; a real OpenRouter end-to-end call remains
  unverified under the repository credential policy.
- `participant.mp4` is visual-only because PulseAudio utilities were not
  available and the Gibbs task has no experiment audio stimulus.
- Human evaluator feedback notes that the test evidence lacks a standard
  procedure for human testing across different AI proportions.
