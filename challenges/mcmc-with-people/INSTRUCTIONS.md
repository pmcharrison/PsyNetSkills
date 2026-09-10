---
title: Markov chain Monte Carlo with people
type: experiment implementation
difficulty: 8
authors: [eandrade-lotero]
---

Implement a PsyNet experiment inspired by Sanborn and Griffiths, "Markov Chain
Monte Carlo with People." The source paper is provided in
`references/sanborn_griffiths_mcmc_people.pdf`.

The experiment should implement the paper's core idea: a participant learns a
category distribution, then chooses between the current state of a Markov chain
and a symmetric proposal. Those choices determine the next chain state, allowing
the experimenter to recover samples from the participant's subjective category
distribution.

## Background

The participant learns to distinguish two categories of schematic fish. "Ocean"
fish are drawn from a broad uniform height distribution. "Fish farm" fish are
drawn from a narrower Gaussian height distribution. After training, the
participant repeatedly answers paired-choice trials asking which of two fish is
more likely to have come from the fish farm. One fish is the current state of an
MCMC chain and the other is a proposal. If the participant chooses the proposal,
the chain moves to that proposal; otherwise the chain remains at its current
state.

## Stimuli

Use simple locally generated visual stimuli; no external image service should be
needed. A fish can be drawn with SVG, HTML/CSS, canvas, or another local method,
but it should vary perceptibly along a single dimension: body height. Other
features, such as length, color, eye position, and tail shape, should remain
fixed so that the category is defined by height.

Represent fish height in a documented continuous or finely discretized numeric
space. The implementation should include the paper's training distributions as
configurable constants:

- Ocean fish: uniform heights bounded by 2.63 cm and 5.76 cm.
- Fish farm fish: Gaussian heights with two possible means, 3.66 cm and
  4.72 cm.
- Fish farm fish: Gaussian standard deviations of 0.13 cm and 0.31 cm.

Assign each participant to one of the four fish-farm conditions created by
crossing the two means and the two standard deviations. If the display uses
pixels, normalized units, or arbitrary SVG units instead of physical
centimeters, document the mapping and preserve the original centimeter values in
trial metadata.

## Procedure

The participant should first complete clear instructions and practice or
training trials that teach the two category labels. Training trials should show
a single fish sampled from either the ocean distribution or the assigned fish
farm distribution. The participant classifies the fish as "ocean" or "fish
farm" and receives feedback.

After initial training, the participant completes interleaved blocks of training
and MCMC trials. The exact block lengths may be shorter than the paper's
laboratory session for local testing, but the implementation should keep the
structure configurable and include a documented paper-like configuration:

1. An initial block of training trials.
2. Repeated MCMC blocks.
3. Refresher training blocks between MCMC blocks.
4. A final no-feedback classification test block.

During each MCMC trial:

1. Select one of three active chains for the participant.
2. Draw a proposal from a symmetric distribution centered on that chain's
   current state. The proposal distribution should have zero probability of
   proposing exactly the current state.
3. Present the current-state fish and proposal fish side by side in randomized
   left-right order.
4. Ask: "Which fish is more likely to have come from the fish farm?"
5. If the participant chooses the proposal, update the chain state to the
   proposal. If the participant chooses the current state, leave the chain
   unchanged.

Initialize the three chains from overdispersed starting values, following the
paper's spirit: one low value, one central value, and one high value. The
paper's starting values were 2.63 cm, 4.20 cm, and 5.76 cm.

## Data recording

Record enough structured data to reconstruct every trial and every chain:

- Participant condition, including fish-farm mean and standard deviation.
- Trial block, trial type, trial index, and reaction time.
- For training and test trials: sampled category, sampled height, participant
  response, correctness, and feedback status.
- For MCMC trials: chain id, previous state, proposal state, accepted state,
  whether the proposal was accepted, left-right assignment, selected side, and
  proposal distribution parameters.
- Any unit conversion used to display centimeter-valued fish heights on screen.

Chain state should be maintained by the experiment logic rather than
post-processed after a set of independent paired choices. A reviewer should be
able to inspect exported trial records and verify that each MCMC trial depends
on the previous accepted state of the same chain.

## Analysis

Include an analysis script or notebook that runs on exported data and on a
documented simulated dataset. The analysis should:

- Plot or summarize the traces of the three chains for each participant.
- Apply a simple burn-in rule, such as discarding samples before the first
  crossing between chains, or use another clearly documented convergence
  heuristic.
- Estimate the recovered fish-farm distribution from retained MCMC samples for
  each participant and each training condition.
- Compare recovered means and standard deviations against the assigned training
  distribution.
- Report acceptance rates and flag chains that hit the boundaries of the
  allowed height range.

The simulated-data workflow should create enough synthetic participants to show
that the analysis can recover the four intended condition differences when
participants behave approximately according to a noisy fish-farm preference
rule.

## Implementation notes

- Keep all participant-facing text translation-ready.
- Keep the experiment runnable locally with PsyNet's standard development
  setup and without production credentials.
- Provide a short `README.md` or methods note in the implemented experiment
  folder explaining how the MCMC chain is represented, how proposals are drawn,
  how local testing shortens or preserves the full paper-like schedule, and how
  to run the analysis.
- Include participant-flow evidence, such as a short screen recording or
  screenshots, showing both a single-fish training trial and an MCMC paired
  choice trial.
