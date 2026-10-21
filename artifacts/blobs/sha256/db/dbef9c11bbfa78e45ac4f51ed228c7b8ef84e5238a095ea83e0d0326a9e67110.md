# README

This experiment is implemented using *PsyNet*, a framework for running behavioral experiments
in-person and over the internet. For comprehensive guidance on running PsyNet experiments,
please visit [PsyNet's documentation website](https://psynetdev.gitlab.io/PsyNet/).

## Hybrid AI participant mode

This attempt adapts the Gibbs sampling demo so it can run in pure-human,
mixed human-AI, or all-AI modes. The default `hybrid_ai_proportion = 0`
preserves the original pure-human behavior; scheduled AI bots are only launched
when the configured proportion is greater than zero.

Set the following values in `config.txt` or with matching `PSYNET_...`
environment variables:

- `hybrid_ai_proportion`: target AI percentage from `0` to `100`.
- `hybrid_target_n_participants`: total participant target for the hybrid run.
- `hybrid_trial_capacity_participants`: participant capacity implied by the
  available Gibbs trials.
- `hybrid_openrouter_api_key_env`: name of the environment variable containing
  the OpenRouter API key; defaults to `OPENROUTER_API_KEY`.
- `hybrid_openrouter_model`, `hybrid_openrouter_base_url`,
  `hybrid_openrouter_timeout`, and `hybrid_openrouter_max_retries`: OpenRouter
  request settings.
- `hybrid_openrouter_mock`: when true, uses a deterministic local mock response
  so local tests never require real credentials.

The human page and AI prompt are built from the same stimulus object: target
word, active color channel, current RGB values, and slider bounds. AI responses
must parse to `{"answer": <integer>}` with a value from 0 to 255 before PsyNet
submits the slider response.
