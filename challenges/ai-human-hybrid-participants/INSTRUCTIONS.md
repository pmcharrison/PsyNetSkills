---
title: AI and hybrid human-AI participants
type: experiment implementation
difficulty: 7
authors: [zeroada]
---

Adapt PsyNet's Gibbs sampling demo, starting from
`~/PsyNet/demos/experiments/gibbs`, so that the experiment can run with pure
human participants, pure AI participants, or any human-AI mixture.

The original Gibbs sampling task should remain the scientific and behavioral
baseline. Human participants should see the same instructions, stimuli, and
response interface as in the original demo unless a change is strictly needed to
support the hybrid condition. When the configured AI participant proportion is
`0`, the experiment should behave like the original pure-human experiment.

Add configuration parameters that control the target proportion of AI
participants from `0` to `100`. These parameters should be documented clearly,
validated, and easy to set from the experiment configuration. The implementation
should also document the configuration needed for OpenRouter API access, such as
the API key environment variable, model name, base URL, and any timeout or retry
settings. Do not commit real API keys or production credentials.

Implement a `bot_response` function that allows an AI agent to complete the same
trial that a human participant would complete. The function should receive or
derive the exact stimulus representation that is shown to the human participant,
format it for the AI model, call OpenRouter with that stimulus, and return an
answer in the same response format expected from a human participant. The code
should handle malformed model output conservatively, for example by validating
and parsing the response before it is submitted to the experiment.

Design the AI prompt so that AI bots receive instructions that match the human
participant instructions as closely as possible. The prompt should explain the
task, present the current stimulus in an unambiguous format, define the required
answer format, and avoid giving the AI any information that a human participant
would not have. The same underlying stimulus values should drive both the human
display and the AI prompt.

Implement a scheduling or assignment mechanism that launches AI bots as needed
to approximate the configured target AI proportion while allowing human
participants to continue through the original flow. The mechanism should be
testable and should not change Gibbs sampling logic apart from deciding whether
a participant is human controlled or AI controlled.

Add tests for the new hybrid behavior. These tests should cover at least the
pure-human setting, nonzero AI proportions, all-AI operation, configuration
validation, prompt/stimulus consistency, and the scheduling logic used to match
the intended AI-human proportion. API-dependent tests should use stubs or mocks
unless a real OpenRouter key is intentionally supplied through the environment.
