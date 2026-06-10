# Evaluation criteria

An attempt should be considered successful if it implements a runnable PsyNet
chain experiment that satisfies the following criteria:

- Uses PsyNet chain nodes to persist one generated website version per node and
  carries the appropriate website context forward through the chain.
- Presents distinct participant-facing flows for the first node, second node,
  and third-or-later nodes, including the comparison choice for third and later
  nodes.
- Calls OpenRouter through configurable settings or environment variables, never
  hard-coding secrets or machine-specific paths.
- Sends the participant instruction and the relevant website context to the AI,
  while saving the AI request and response in a form that excludes secrets.
- Safely renders generated website output inside the experiment page.
- Saves enough node and trial data to reconstruct the chain history, including
  participant instructions, comparison choices, selected website context, raw AI
  responses, and generated website versions.
- Includes bots, tests, or another simple automated path that verifies the main
  experiment flow without requiring live OpenRouter credentials by default.
- Provides evidence that the experiment can run locally and that the first-node,
  second-node, and later-node flows behave as specified.
