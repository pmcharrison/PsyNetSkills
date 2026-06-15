# Report

## Summary

This attempt adapts PsyNet's Gibbs sampling demo into a configurable hybrid
human-AI experiment. The runnable experiment is in `code/gibbs_hybrid/` and
keeps the original group-choice page, color-slider Gibbs trials, repeat trials,
consistency feedback path, and custom export table.

## Implementation

- Added `ai_participant_proportion`, participant target, scheduler, and
  OpenRouter configuration keys in `config.txt`.
- Registered custom config keys in `Exp.extra_parameters` and validated bounds,
  scheduler settings, timeout/retry settings, model/base URL, and credential
  availability when live OpenRouter mode is enabled.
- Built a shared `build_color_stimulus(...)` helper that feeds both the human
  `ColorSliderPage` prompt and the AI prompt.
- Added a `color_slider_bot_response(...)` path that uses deterministic mock
  OpenRouter responses by default, or live OpenRouter calls when configured with
  an environment-supplied API key.
- Added strict JSON parsing for model output so only `{"value": <int 0..255>}`
  can be submitted as a slider response.
- Added deterministic bot assignment for local tests and active scheduler
  helpers for incremental AI launches in live mixed sessions.

## Validation

- `pytest test_hybrid.py` passed for config validation, prompt/stimulus parity,
  parser strictness, mock OpenRouter behavior, scheduler launch counts, and
  deterministic bot assignment.
- `python experiment.py` passed.
- `psynet test local` passed with the default pure-human configuration.
- Temporary-config `psynet test local` checks passed at `50%` AI and `100%` AI.
- `psynet simulate` with a temporary `50%` AI configuration generated
  `evidence/simulated_data.zip`, verified to contain `4` human and `4` mock-AI
  participants.
- `evidence/analyses/analysis.ipynb` executed successfully and confirms the
  controller mix, finalized trial count, and mock-AI response metadata.
- `psynet performance-test local` completed for 40 concurrent bots with zero
  bot errors and zero request errors; output is in `evidence/performance.json`.
- Playwright generated participant-flow screenshots and
  `evidence/participant.mp4` from a local debug server.
- `evidence/monitor.html` contains a dashboard/develop snapshot from the local
  debug run.

## Limitations

The default evidence uses deterministic mock OpenRouter behavior, not paid or
networked model calls. This validates the prompt, parser, scheduler, and data
paths without storing real API credentials or provider logs. A live OpenRouter
smoke test should be run separately only when a safe API key is intentionally
provided through the configured environment variable.
