# Portfolio website chain

This PsyNet experiment implements an across-participant chain in which each
participant writes one instruction for an AI model to create or revise a
portfolio website.

The experiment reads OpenRouter settings from environment variables, and also
checks same-named Dallinger config values if a deployment registers them:

- `openrouter_api_key` / `OPENROUTER_API_KEY`
- `openrouter_model` / `OPENROUTER_MODEL`
- `openrouter_base_url` / `OPENROUTER_BASE_URL`
- `openrouter_timeout_seconds` / `OPENROUTER_TIMEOUT_SECONDS`

When no API key is available, or the configured model cannot be listed, the
experiment uses the deterministic fallback path and stores the fallback reason in
the generated node definition.
