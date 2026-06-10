---
title: AI condition and human-AI hybrid design
type: experiment implementation
difficulty: 8
authors: [zeroada]
---

Implement a PsyNet experiment that extends the existing pure-human "Gibbs
Sampling with People" demo into a configurable human-AI hybrid experiment. The
implementation should preserve the original experiment as the baseline case
while allowing some or all participant decisions to be supplied by an AI agent.

The experiment should:

- Start from the behavior of the Gibbs Sampling with People PsyNet demo, using
  the same task structure and stimulus presentation as the human version.
- Add a configurable AI-participant condition that can generate trial responses
  without changing the participant-facing workflow used by humans.
- Allow the experimenter to set the desired AI share among participants anywhere
  from 0% to 100%.
- Support hybrid runs in which human and AI participants contribute to the same
  experimental process according to the configured proportion.
- Clearly record, for each participant and trial, whether the response came from
  a human or from the AI condition.
- Keep the 0% AI setting equivalent to the original pure-human experiment, with
  no changes to the original sampling logic or human participant experience.
- Include a short analysis or inspection script that summarizes the resulting
  human, AI, and hybrid contributions from exported or simulated data.

The goal is a runnable PsyNet demo that makes AI participation an experimental
condition rather than a separate experiment. The AI behavior can be implemented
with a lightweight local policy or mock model suitable for testing, provided the
interface is clear enough that a real language-model-backed participant could be
substituted later without redesigning the experiment.
