---
score: 6
---

# Evaluation

## Summary

The evaluator rated the attempt 6/10. The implementation is clear and
configuration-focused, with useful local fallback behavior and real PsyNet bots,
but the AI-human scheduling strategy is not acceptable for the challenge because
it launches the full AI quota as soon as one human enters. Those AI agents can
consume the Gibbs trials before humans receive participant-facing trials, making
the observed 50/50 condition badly unbalanced.

## Strengths

- Tunable parameters are placed cleanly in `config.txt`.
- The implementation provides a pseudo API/fallback path when OpenRouter credentials are missing.
- The attempt launches real PsyNet bot participants to reach an AI-human target proportion.
- The implementation is clear and easy to inspect.

## Weaknesses

- The scheduler does not randomly assign or otherwise actively balance AI and human participation as required.
- The current implementation launches all needed AI agents once the first human enters, which produces an unbalanced session.
- The apparent crash after a human attempt is caused by the AI agents quickly consuming the desired Gibbs sampling trials; PsyNet then considers the experiment complete and shuts down the local debug server.
- The experiment parameters should be set so the total participant target and available Gibbs trials are compatible; humans should not be starved of trials by fast AI bots.
- `psynet debug local --legacy` exits once the experiment completes, so it is not suitable when the researcher expects the dashboard to remain available after completion.

## Criteria

- [x] The attempt starts from the PsyNet Gibbs sampling demo and preserves the original pure-human behavior when the AI participant proportion is `0`.
- [x] AI proportion configuration accepts the full `0` to `100` range, rejects invalid values, and is documented together with required OpenRouter settings.
- [x] The implementation contains a `bot_response` path that uses the same stimulus values shown to human participants, calls OpenRouter through configurable credentials, parses the model response, and submits data in the original experiment response format.
- [x] The AI prompt closely matches the human-facing instructions, specifies the required output format, and does not reveal extra information unavailable to human participants.
- [x] Human and AI trial presentation are kept consistent by deriving both the human display and AI prompt from the same trial data rather than maintaining divergent stimulus definitions.
- [ ] The scheduling or assignment logic launches AI participants in a way that tracks the configured target proportion across mixed human-AI sessions.
- [x] Tests or executable checks cover pure-human, mixed, and all-AI settings, configuration validation, prompt/stimulus consistency, scheduler behavior, and OpenRouter calls using mocks or environment-supplied credentials.
- [x] The solution avoids committing real API keys, production credentials, or unrelated changes to the shared PsyNet checkout.

## Notes

- Score and feedback should come from a human evaluator, captured
  conversationally when working with Cursor Cloud Agents.
- Real OpenRouter end-to-end verification was not run because challenge work in this repository must not use custom or production service credentials. Local tests cover the OpenRouter prompt/parsing path and use the deterministic fallback when no key is present.
- `agent.json` currently uses `pmcharrison` as the attempt author because no author key was provided during implementation; update it if a different human author should be credited.
- Human evaluator feedback: "put tunable parameters in config.txt, making it very clean"; "set up pseudo API call when credential is missing"; "launch real bot to reach the AI-human proportion"; "clear implementations."
- Human evaluator feedback: the AI-human scheduling needs to be rewritten as an active scheduler algorithm that randomly assigns or otherwise properly matches the desired proportion over time, instead of launching all AI participants as soon as one human enters.
