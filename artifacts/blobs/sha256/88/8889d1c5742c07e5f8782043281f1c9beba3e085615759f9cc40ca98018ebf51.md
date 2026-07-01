# Evaluation criteria

- The attempt starts from the PsyNet Gibbs sampling demo and preserves the
  original pure-human behavior when the AI participant proportion is `0`.
- AI proportion configuration accepts the full `0` to `100` range, rejects
  invalid values, and is documented together with required OpenRouter settings.
- The implementation contains a `bot_response` path that uses the same stimulus
  values shown to human participants, calls OpenRouter through configurable
  credentials, parses the model response, and submits data in the original
  experiment response format.
- The AI prompt closely matches the human-facing instructions, specifies the
  required output format, and does not reveal extra information unavailable to
  human participants.
- Human and AI trial presentation are kept consistent by deriving both the human
  display and AI prompt from the same trial data rather than maintaining
  divergent stimulus definitions.
- The scheduling or assignment logic launches AI participants in a way that
  tracks the configured target proportion across mixed human-AI sessions.
- Tests or executable checks cover pure-human, mixed, and all-AI settings,
  configuration validation, prompt/stimulus consistency, scheduler behavior, and
  OpenRouter calls using mocks or environment-supplied credentials.
- The solution avoids committing real API keys, production credentials, or
  unrelated changes to the shared PsyNet checkout.
