---
score: 6
---

# Evaluation

## Summary

Score: 6/10. The attempt implements the core chain mechanics and evidence path,
but the participant-facing instructions are not clear enough for a general
public audience, and the testing evidence should include a participant actually
using or inspecting the generated website before providing feedback.

## Strengths

- Implements the main PsyNet chain flow with first-node creation, second-node
  improvement, and third-node comparison evidence.
- Provides automated fallback-path tests, local PsyNet test evidence, performance
  evidence, and refreshed three-participant participant-flow evidence.

## Weaknesses

- Participant-facing instructions are hard to read and not clear enough for the
  general public.
- The manual test evidence does not show participants trying to use the generated
  portfolio website before giving improvement feedback.

## Criteria

Copied from `challenge/CRITERIA.md` for human review:

- [x] Uses PsyNet chain nodes to persist one generated website version per node and carries the appropriate website context forward through the chain.
- [x] Presents distinct participant-facing flows for the first node, second node, and third-or-later nodes, including the comparison choice for third and later nodes.
- [x] Calls OpenRouter through configurable OpenAI-compatible settings or environment variables, never hard-coding secrets or machine-specific paths.
- [x] Checks for an API key and configured model availability before live AI calls, then falls back to a general `bot_response` path when either is unavailable.
- [x] Sends the participant instruction and the relevant website context to the AI, while saving the AI request and response in a form that excludes secrets.
- [x] Saves whether live AI or fallback generation was used for each node, including the fallback reason when applicable.
- [x] Safely renders generated website output inside the experiment page.
- [x] Saves enough node and trial data to reconstruct the chain history, including participant instructions, comparison choices, selected website context, raw AI responses, and generated website versions.
- [x] Includes bots, tests, or another simple automated path that verifies the main experiment flow, including the no-key or no-model fallback, without requiring live OpenRouter credentials by default.
- [x] Clearly informs the user in the attempt summary when fallback generation was used because an API key or model was unavailable.
- [~] Provides evidence that the experiment can run locally and that the first-node, second-node, and later-node flows behave as specified. The three-stage evidence exists, but the test walkthrough should show participants using or inspecting the generated website more deliberately before feedback.

## Notes

- Score and feedback should come from a human evaluator, captured
  conversationally when working with Cursor Cloud Agents.
- Fallback generation was used for automated tests and evidence because no OpenRouter API key/model credentials were configured, consistent with the challenge credential policy.
- `evidence/participant.mp4` is a visual recording only; the experiment does not produce audio. It shows three separate participant profiles progressing through first-node creation, second-node improvement, and third-node comparison/instruction flows.
- `evidence/performance.json` and `evidence/performance-test.log` come from `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0`.
- Human feedback: "the instruction is not clear enough and is hard to read for the general public. Also there should be an attempt of using the website before giving the feedback when testing the experiment."
