# README

This experiment is implemented using *PsyNet*, a framework for running behavioral experiments
in-person and over the internet. For comprehensive guidance on running PsyNet experiments,
please visit [PsyNet's documentation website](https://psynetdev.gitlab.io/PsyNet/).

## Hybrid AI participant settings

This attempt adapts PsyNet's Gibbs sampling demo so the original human flow can
run unchanged while PsyNet bot participants can act as AI-controlled
participants.

- `ai_participant_proportion`: target AI percentage, from `0` to `100`.
  `0` keeps the experiment in pure-human mode; `100` requests all AI-controlled
  participants.
- `ai_target_total_participants`: target total participant count used when
  automatically launching AI bots. Leave this at `0` to disable automatic
  launches.
- `openrouter_api_key_env`: name of the environment variable containing the
  OpenRouter API key. The default is `OPENROUTER_API_KEY`.
- `openrouter_model`: OpenRouter model name, defaulting to
  `openai/gpt-4o-mini`.
- `openrouter_base_url`: OpenRouter chat completions endpoint.
- `openrouter_timeout_seconds` and `openrouter_max_retries`: request timeout and
  retry controls.
- `openrouter_mock_when_missing_key`: `true` uses a deterministic local fallback
  when no key is present, which is useful for tests. Set it to `false` for real
  AI runs so missing OpenRouter credentials fail closed.

The AI prompt is built from the same stimulus values that define the human color
slider page: target word, participant group, active RGB channel, and starting RGB
values. Model output is parsed and validated as an integer in `[0, 255]` before
submission.
