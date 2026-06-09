# Learnings

## Pin generated experiment requirements to the recorded PsyNet commit

The standard PsyNet demo scaffold uses `master` in `requirements.txt` and
`constraints.txt`, but an attempt records a specific PsyNet checkout. Pinning the
generated experiment to that commit makes later review and reruns match the
metadata more closely.

*Actions:*
- **PsyNetSkills:** Update the attempt workflow notes to recommend pinning generated experiment requirements to the recorded PsyNet commit. Confidence: medium. Status: considering.

## Simulated partners simplify repeated-game challenge evidence

The public challenge asks for a clearly described partner, not necessarily a
live synchronized participant. A deterministic simulated partner keeps the
participant experience clear while avoiding local multi-participant grouping
fragility during evidence collection.

*Actions:*
- **PsyNetSkills:** For future game challenges, specify whether a partner should be simulated or another live participant when that distinction matters for evaluation. Confidence: high. Status: considering.

## Prefer structured tags over raw markup in instruction pages

A browser probe caught a payoff list rendered as escaped HTML when raw markup was
nested inside a `dominate` container. Using `tags.ul` and `tags.li` kept the
instructions visible as an actual list.

*Actions:*
- **PsyNetSkills:** Add a validation reminder for participant-facing challenge evidence to inspect instruction pages for escaped HTML. Confidence: medium. Status: considering.

## Static trial makers shuffle blocks unless ordered explicitly

The first participant recording showed rounds in the order 2, 1, 3, 4, 5 because
`StaticTrialMaker` inherits a randomized default `choose_block_order`. Repeated
game rounds should use explicit blocks plus a sorted block order when the visible
round sequence matters.

*Actions:*
- **PsyNetSkills:** Add a note to experiment implementation guidance that ordered repeated tasks need explicit block ordering or a timeline loop. Confidence: high. Status: considering.
