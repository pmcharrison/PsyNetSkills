# AI-hybrid Gibbs demo

This experiment extends PsyNet's Gibbs Sampling with People demo with a configurable AI-response condition. The participant-facing workflow and Gibbs trial maker remain the same as the original demo; the AI condition is assigned invisibly at participant initialization and is used only by automated bot/AI participants.

## Configuration

Set the desired AI share with the `AI_SHARE` environment variable:

- `AI_SHARE=0` keeps the original pure-human baseline path.
- `AI_SHARE=0.5` creates a hybrid run with an approximate 50/50 split.
- `AI_SHARE=1` routes every participant through the local AI policy.

The local AI policy is deterministic and target-aware, but deliberately small. It can be replaced with a language-model-backed policy by implementing the same `choose(...)` interface in `experiment.py`.

## Running

```bash
AI_SHARE=0.5 psynet test local
AI_SHARE=0.5 psynet debug local
python analyze_contributions.py --simulate --ai-share 0.5
```

Each participant receives `participant.var.response_source` and `participant.var.ai_share`. Each finalized trial receives matching `trial.var.response_source`, `trial.var.ai_share`, and, for AI trials, `trial.var.ai_policy`.
