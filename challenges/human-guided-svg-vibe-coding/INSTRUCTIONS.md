---
title: Human-guided SVG vibe coding
type: experiment implementation
difficulty: 8
authors: [haoyu-hu]
---

Implement a PsyNet experiment that reproduces the main human-led vibe-coding
condition from Hu et al. (2026), "Why Human Guidance Matters in Collaborative
Vibe Coding." The paper is summarized in
`references/hu_et_al_2026_vibe_coding.md`; verify this reference before
proceeding.

The experiment should study how human participants guide an AI coding assistant
to iteratively recreate a reference image as SVG code. In this challenge, human
participants perform both participant-facing roles from the main experiment:
they select which SVG rendition is currently better and provide
natural-language instructions for the next improvement. The AI acts only as the
coding assistant that converts those instructions into SVG code.

## Stimuli and chain design

Use a set of reference animal images inspired by the paper's ten target
categories: cat, dog, tiger, bird, elephant, penguin, shark, zebra, giraffe, and
panda. A local demonstration may use a smaller subset with simple generated or
hand-authored images, but the stimulus loader should make it clear how to scale
to the full set.

Each chain should attempt to recreate one reference image over repeated
iterations. The paper's main condition used 30 chains, corresponding to three
repeats of each of the ten reference images, and 15 iterations per chain. The
implementation should expose configuration parameters for these values so that
attempts can run a short deterministic local demo while preserving the full
study structure.

## Human-led participant flow

Participants should see the rendered reference image throughout the task. In the
first iteration, no previous SVG rendition exists, so the participant writes
natural-language guidance for the AI coding assistant based only on the
reference image. The AI coding assistant returns SVG code, which is rendered
back to an image and stored as the first candidate.

In the second iteration, the participant should see the reference image and the
current best SVG rendition, then write another natural-language instruction for
the AI coding assistant. No explicit selection is required yet, because there is
not enough history for a meaningful comparison.

From the third iteration onward, the participant should first act as selector.
They compare the reference image, the previous best SVG rendition, and the most
recent AI-generated candidate. They choose which rendition better matches the
reference image. The selected rendition becomes the current best image. The same
participant then acts as instructor, writing a short natural-language
instruction for how the AI coding assistant should improve the selected SVG on
the next generation step.

Human-facing copy should make clear that participants are not expected to write
SVG code themselves. They should be encouraged to give concise, high-level
guidance about visual changes, for example changes to body shape, proportions,
colors, missing features, or incorrect details.

## AI coding assistant

Isolate SVG generation behind a documented client interface. The client should
receive the same task state that motivates the human instruction: the reference
image identifier, the selected or current SVG code, the rendered SVG image when
available, and the participant's natural-language instruction.

Attempts must run locally without real service credentials. Provide a
deterministic mock coding assistant that produces valid SVG code and visibly
changes across iterations. A real model provider may be documented as an
optional mode, but API keys, production credentials, and real paid-service
configuration must not be committed.

Generated SVG should be handled conservatively. Sanitize or sandbox rendered SVG
outputs, record render failures, and avoid treating invalid SVG as a successful
candidate. If an invalid candidate is shown in a local demo, the failure state
should be explicit and stored in the trial data.

## Data to store

Store enough structured data to reconstruct each chain:

- reference image identifier and stimulus metadata;
- chain identifier, iteration number, and configured chain length;
- participant identifier or anonymous participant role metadata;
- selector choice from iterations where selection is available;
- previous best SVG identifier, new candidate SVG identifier, and selected SVG
  identifier;
- human instruction text submitted to the AI coding assistant;
- generated SVG code, rendered output path or render-error state, and generation
  timestamp;
- AI coding assistant mode, model name when applicable, prompt metadata, and
  mock/real provider settings;
- any post-task survey responses about participant strategy or technical
  problems.

The saved data should make it possible to plot chain progress by iteration and
to inspect how human instructions relate to accepted or rejected SVG candidates.

## Independent similarity evaluation

Implement a separate evaluator task or mode for rating the quality of generated
SVG outputs. Evaluators should see one reference image and one rendered SVG
output at a time, then rate visual similarity on a clearly labeled numeric
scale. They should not see the instructor text, selector choice, model metadata,
chain condition labels, or any other information that would reveal how the SVG
was produced.

For local testing, include a small evaluation set sampled from the generated
chain outputs. The resulting data should support summarizing similarity ratings
by reference image and iteration. A full reproduction of the paper's bootstrap
analysis is not required.

## Local demonstration and evidence

The submitted attempt should include a runnable local demonstration with the
deterministic mock coding assistant. The demo should show at least one complete
multi-iteration chain, including:

- a first instruction based on the reference image alone;
- a later instruction based on the current best SVG rendition;
- a selection step where the participant chooses between the previous best and
  the newly generated candidate;
- an AI-generated SVG candidate that is rendered and stored;
- the selected SVG being carried forward to the next iteration;
- at least one independent evaluator similarity-rating trial.

Attempt evidence should demonstrate that the human participant flow, SVG
rendering, selection state, mock AI generation, and evaluator task all run
end-to-end without external credentials.
