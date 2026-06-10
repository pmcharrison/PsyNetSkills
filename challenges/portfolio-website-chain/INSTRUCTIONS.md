---
title: Portfolio website chain experiment with human instructions and AI editing
type: experiment implementation
difficulty: 7
authors: [Haoyu-Hu]
---

Implement a PsyNet chain experiment in which participants collaboratively create
and improve a portfolio website with the help of an AI model. Each participant
contributes one instruction to the chain. The instruction is sent to an AI model
through the OpenRouter API, and the model returns a new or revised portfolio
website. Each node in the chain should store the participant instruction, the AI
request, the AI response, the generated website, and enough metadata to
reconstruct the chain history.

The participant flow should depend on the position of the node in the chain:

- For the first node, explain that the participant is creating a portfolio
  website with AI assistance. Ask the participant to write an instruction for the
  AI that will produce the first version of the website.
- For the second node, show the original task instruction and the website created
  in the previous round. Ask whether the participant has suggestions to improve
  the website, then ask them to write an instruction for the AI.
- For the third and later nodes, first show the website from the previous round
  and the website from two rounds earlier. Ask the participant to choose which
  website they think is better. Then show the original task instruction and the
  selected website, and ask the participant to write an instruction for the AI to
  improve the selected website.

Use a PsyNet chain structure where each node stores the website version created
at that point in the chain. The chain should make the current node's AI prompt
from the participant's instruction and the relevant selected website context. For
the first node, this context is the original portfolio website task. For the
second node, it is the website from the previous round. For later nodes, it is
the participant-selected website from the recent comparison.

Use OpenRouter for AI API calls. Load the API key and any configurable model or
API settings from configuration or environment variables. Do not hard-code API
keys, service credentials, local paths, or machine-specific configuration. Tests
and bots should not require live credentials unless they are explicitly supplied
through the environment.

Render generated portfolio websites safely inside the experiment page. The
participant should be able to inspect the generated website without giving the
model output unrestricted access to the parent experiment page. The
implementation should handle malformed, empty, or unsafe AI output
conservatively, while still saving the raw AI response for reconstruction and
debugging.

Save all trial data needed to reconstruct the experiment history. At minimum,
each node should save:

- the node position and relevant parent node identifiers;
- the original participant-facing portfolio task instruction;
- the participant's free-text instruction;
- the selected comparison winner for third and later nodes;
- the website context sent to the AI;
- the complete AI request payload, excluding secrets;
- the complete AI response payload;
- the generated website version used for display in the next node; and
- timestamps or other useful metadata for diagnosing the chain.

Include clear participant-facing instructions for each node type. The language
should make the participant's role concrete: they are not writing website code
directly, but instructing the AI on what portfolio website to create or improve.
After enough history exists, participants should understand that their comparison
choice determines which recent website version is carried forward.

Include a bot or other simple automated test path that exercises the main
experiment flow. The test path should cover creating the first website version,
improving an existing version, comparing two recent versions, saving the
comparison choice, and producing the next AI request from the selected context.
API-dependent behavior should be tested with a stub or mock response unless live
OpenRouter credentials are intentionally provided.
