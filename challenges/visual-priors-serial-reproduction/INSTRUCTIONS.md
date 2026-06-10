---
title: Visual priors serial reproduction
type: experiment implementation
difficulty: 9
authors: [pmcharrison]
---

Implement a PsyNet experiment that recreates the spatial-memory serial
reproduction study described by Langlois, Jacoby, Suchow, and Griffiths (2017),
"Uncovering visual priors in spatial memory using serial reproduction." The
source paper is provided in `references/`.

The experiment should implement the participant-facing procedure as a real
serial reproduction task. Participants view a small black dot inside a geometric
outline, remember its location after a delay, and then reproduce the dot by
clicking inside the same shape. The response from one participant becomes the
stimulus for the next participant in the chain.

The experiment should:

- Use the paper as the primary specification, including the Methods section,
  figure captions, and any details recoverable from the supplied reference.
- Implement the Experiment 1 shape set: circle, equilateral triangle, square,
  vertical oval, horizontal oval, and regular pentagon.
- Include a documented Experiment 2-style configuration for regular polygons
  with more than five vertices. If the exact vertex counts cannot be recovered
  from the supplied paper excerpt, choose a reasonable configurable set and state
  the assumption clearly.
- Render each stimulus as an approximately 400 x 400 px image or canvas with a
  6 px black outline on a white background, and place the stimulus inside a
  larger canvas whose screen position is randomized across trials.
- Generate or load initial seed dots inside each shape. The implementation
  should support the scale reported in the paper, including 400 seeds for the
  circle and 500 seeds for each other Experiment 1 shape, while allowing a
  smaller local-test mode for development.
- Implement serial reproduction chains with 10 iterations. Each chain should
  preserve shape identity, seed identity, generation number, previous dot
  location, participant response location, response time, and accuracy metadata.
- Assign each participant to trials for exactly one experimental shape, matching
  the paper's between-participant shape design unless a documented local-test
  mode intentionally reduces this for speed.
- Include 10 practice trials using a circle. Practice trials should present the
  dot for 4000 ms, show a blank interval for 1000 ms, then show the circle
  without the dot until the participant clicks a remembered location.
- Include 95 experimental trials for the assigned shape. Experimental trials
  should present the dot for 1000 ms, use the same response workflow as the
  practice trials, and prevent participants from contributing multiple responses
  within the same serial reproduction chain.
- Allow participants to reposition the response dot before confirming the trial,
  as described in the paper.
- Provide trial-by-trial feedback using the paper's acceptance rule: responses
  within 8% of the displayed shape's width and height should receive green
  "This was accurate" feedback and bonus-credit metadata; otherwise, responses
  should receive red "This was not accurate" feedback and be excluded from chain
  propagation.
- Save enough structured data to reconstruct every chain, every presented
  stimulus, each participant's raw click coordinates, normalized coordinates
  within the shape, feedback outcome, timing information, randomized display
  offset, and whether the trial was propagated or discarded.
- Include clear participant instructions, informed-consent placeholder text,
  practice/main transition pages, and a completion page suitable for local PsyNet
  testing.
- Include automated bots or test helpers that can run through the experiment
  locally and exercise both accepted and rejected responses.
- Include an analysis script or notebook that can load exported PsyNet data,
  reconstruct chain generations by shape and seed, plot the final-generation
  response clouds, estimate two-dimensional kernel densities, and compute at
  least one convergence measure such as Jensen-Shannon divergence between
  generations.
- Include a simulated-data workflow so the analysis can run without recruiting
  hundreds of participants. The simulated data should preserve the expected
  schema and demonstrate convergence-like behavior toward shape-dependent
  prototypes.
- Include a detailed `README.md` or methods note for the implemented experiment.
  The note should cite the supplied paper for every major design choice, state
  any deviations required for local PsyNet testing, and explain how to run the
  experiment, simulated data generation, and analysis.

Do not use custom or real service credentials. The experiment should run
locally with PsyNet's standard development setup.
