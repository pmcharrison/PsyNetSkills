---
score:
---

# Evaluation

## Summary

Summarize the human evaluator's overall judgment.

## Strengths

- 

## Weaknesses

- 

## Criteria

- [ ] Uses PsyNet chain nodes to persist one generated website version per node
  and carries the appropriate website context forward through the chain.
- [ ] Presents distinct participant-facing flows for the first node, second
  node, and third-or-later nodes, including the comparison choice for third and
  later nodes.
- [ ] Calls OpenRouter through configurable OpenAI-compatible settings or
  environment variables, never hard-coding secrets or machine-specific paths.
- [ ] Checks for an API key and configured model availability before live AI
  calls, then falls back to a general `bot_response` path when either is
  unavailable.
- [ ] Sends the participant instruction and the relevant website context to the
  AI, while saving the AI request and response in a form that excludes secrets.
- [ ] Saves whether live AI or fallback generation was used for each node,
  including the fallback reason when applicable.
- [ ] Safely renders generated website output inside the experiment page.
- [ ] Saves enough node and trial data to reconstruct the chain history,
  including participant instructions, comparison choices, selected website
  context, raw AI responses, and generated website versions.
- [ ] Includes bots, tests, or another simple automated path that verifies the
  main experiment flow, including the no-key or no-model fallback, without
  requiring live OpenRouter credentials by default.
- [ ] Clearly informs the user in the attempt summary when fallback generation
  was used because an API key or model was unavailable.
- [ ] Provides evidence that the experiment can run locally and that the
  first-node, second-node, and later-node flows behave as specified.

## Notes

- Score and feedback should come from a human evaluator, captured
  conversationally when working with Cursor Cloud Agents.
- Local validation uses the deterministic fallback backend because no safe
  OpenRouter API key or model access is configured in this environment. Live
  OpenRouter behavior remains unverified until safe credentials are supplied.
- `evidence/participant.mp4` is video-only; the experiment does not produce
  audio, so no experiment audio stream is expected.
- `evidence/performance.json` was generated with 40 concurrent bots for 5
  minutes. The final run reported zero bot errors and 1.557s p95 HTTP response time,
  with some bots still running when the fixed-duration test ended.
