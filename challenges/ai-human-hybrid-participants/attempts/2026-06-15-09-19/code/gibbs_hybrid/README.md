# Hybrid Gibbs demo

This experiment is implemented using *PsyNet*, a framework for running behavioral experiments
in-person and over the internet. For comprehensive guidance on running PsyNet experiments,
please visit [PsyNet's documentation website](https://psynetdev.gitlab.io/PsyNet/).

This attempt adapts PsyNet's Gibbs sampling demo so participant sessions can be
human-controlled, AI-controlled through OpenRouter, or a configured mixture of
both. The default configuration keeps `ai_participant_proportion = 0` and
`openrouter_mock_mode = true`, which preserves the original pure-human behavior
and allows local tests to run without real service credentials.

To use live OpenRouter calls, set `openrouter_mock_mode = false` and provide the
API key through the environment variable named by `openrouter_api_key_env`
(default `OPENROUTER_API_KEY`). Do not store real API keys in `config.txt`.
