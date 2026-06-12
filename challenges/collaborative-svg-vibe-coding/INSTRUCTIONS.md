---
title: Collaborative SVG vibe coding
type: experiment implementation
difficulty: 9
authors: [haoyu-hu]
---

Implement a PsyNet experiment that replicates the main collaborative vibe-coding
paradigm from Hu et al. (2026), "Why Human Guidance Matters in Collaborative
Vibe Coding." The paper should be represented in
`references/literature/hu_et_al_2026_vibe_coding.md`; verify this file before
proceeding.

The experiment should study how humans and AI agents iteratively guide an AI
code generator to recreate a reference image as SVG code. A local implementation
does not need to reproduce the paper's full recruitment scale, model fleet, or
analysis pipeline, but it should faithfully implement the participant-facing
workflow and the role structure of the main experiment.

## Core task

Use a small set of reference animal images inspired by the paper's ten target
categories: cat, dog, tiger, bird, elephant, penguin, shark, zebra, giraffe, and
panda. For local testing, the images may be simple generated or hand-authored
assets, but the stimulus loader should make it straightforward to replace them
with a larger study set. The reference images should be displayed to
participants as images, not as SVG source code.

Each chain attempts to recreate one reference image through iterative SVG
generation. On every iteration, an instructor sees the reference image and the
best SVG rendition carried forward from the previous iteration. The instructor
then writes natural-language guidance for an AI code generator. The code
generator returns SVG code, which is rendered back to an image for comparison.

The first iteration should start without a previous SVG rendition. The second
iteration should present only the first generated SVG as the current best
candidate, because there is not yet an alternative to compare. Later iterations
should include an explicit selection step: a selector compares the previous best
SVG rendition with the newly generated rendition and chooses which version is
carried forward to the next instructor.

## Human and AI roles

The implementation should support at least these role-allocation conditions:

1. Human-led chains, where human participants act as both instructor and
   selector.
2. AI-led chains, where an AI agent acts as both instructor and selector.
3. Hybrid chains, where each instructor and selector role can be assigned to a
   human or AI agent according to configurable probabilities.

Configuration should make it easy to run short local demonstrations with a small
number of images, chains, and iterations, and also to approximate the paper's
main design with repeated chains and 15 iterations per chain. The role assigned
at each iteration should be stored with the data so that the chain can be
reconstructed later.

AI instructors should receive the same visual-task information that a human
instructor receives: the reference image and the current best SVG rendition.
When practical, provide the rendered images to the model; if a local mock mode
is used, it should still consume the same structured task representation. AI
selectors should compare the previous best and current candidate using the same
selection question shown to humans. AI code generation should be isolated behind
a clearly documented client interface so attempts can run with a deterministic
mock generator during tests and with a real provider only when an API key is
intentionally supplied through the environment. Do not commit real API keys or
production credentials.

## Participant-facing instruction and selection flow

Human instructors should receive concise instructions explaining that their goal
is to improve the SVG image so that it resembles the reference image more
closely. They should be told to write high-level natural-language guidance for a
coding assistant, not to write SVG code themselves unless they choose to.

Human selectors should see the reference image, the previous best SVG rendition,
and the newly generated SVG rendition side by side. The UI should ask which SVG
better matches the reference image and should allow the selector to choose
either version. The chosen SVG code and rendered image become the chain state for
the next iteration.

Store enough data to reconstruct each chain, including:

- reference image identifier;
- chain identifier and iteration number;
- instructor role and selector role;
- natural-language instructor guidance;
- generated SVG code;
- rendered SVG output or render-error state;
- selector choice and optional selector reasoning;
- previous and selected SVG identifiers;
- model name, prompt metadata, mock/real provider mode, and relevant generation
  settings when AI agents are used.

Malformed or unsafe SVG output should be handled conservatively. The
implementation should sanitize or sandbox rendered SVGs, show clear errors when
generation fails, and avoid advancing invalid SVG code as a successful image
unless the selector deliberately chooses it under a documented failure state.

## Independent similarity evaluation

Implement a separate evaluator task that can be run after or alongside the chain
task. Evaluators should see one reference image and one generated SVG rendition
at a time, then rate their visual similarity on a clearly labeled numeric scale.
The evaluator task should be independent from the instructor/selector task so
that evaluators do not see the prompts, model metadata, or condition labels that
produced the SVG.

The saved evaluation data should support plotting similarity ratings across
iterations and comparing human-led, AI-led, and hybrid chains. It is sufficient
for the challenge to produce clean structured outputs and a small local summary
script; a full statistical replication of every figure in the paper is not
required.

## Local demonstration and evidence

The submitted attempt should include a runnable local demonstration with
deterministic mock AI behavior. The demo should show at least one complete chain
with multiple iterations, including a selection step where the previous or
current SVG is chosen and carried forward. It should also show at least one
similarity-rating trial from the independent evaluator task.

Attempt evidence should demonstrate that:

- reference images and rendered SVG candidates are visible to participants;
- instructors submit natural-language guidance;
- SVG code is generated, rendered, stored, and carried forward across
  iterations;
- selectors can compare previous and current candidates and choose which one
  advances;
- human-led, AI-led, and hybrid role configurations are represented in saved
  data;
- evaluator ratings are collected without revealing condition labels;
- mock AI mode works without external credentials, and any real provider mode is
  documented but optional.

