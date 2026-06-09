# Learnings

## Pin generated experiment requirements to the recorded PsyNet commit

The standard PsyNet demo scaffold uses `master` in `requirements.txt` and
`constraints.txt`, but an attempt records a specific PsyNet checkout. Pinning the
generated experiment to that commit makes later review and reruns match the
metadata more closely.

*Actions:*
- **PsyNetSkills:** Update the attempt workflow notes to recommend pinning generated experiment requirements to the recorded PsyNet commit. Confidence: medium. Status: considering.

## Repeated game challenges need explicit partner semantics

The first attempt used a deterministic simulated partner because the public
instructions did not specify whether the partner had to be another participant.
Human evaluation clarified that this challenge should require live,
synchronised participant pairs.

*Actions:*
- **PsyNetSkills:** Clarify the public challenge instructions to require pairs of real synchronised participants, 10 rounds per pair, and a bonus proportional to points won. Confidence: high. Status: completed. Notes: Implemented after human evaluation feedback on the 2026-06-09-15-35 attempt.

## Review payoff tables for both correctness and presentation

A browser probe caught a payoff list rendered as escaped HTML when raw markup was
nested inside a `dominate` container. Using `tags.ul` and `tags.li` kept the
instructions visible as an actual list, but the evaluator still found the payoff
table aesthetically weak. Participant-facing payoff matrices need both correct
rendering and careful visual formatting.

*Actions:*
- **PsyNetSkills:** Add a validation reminder for participant-facing challenge evidence to inspect instruction pages and payoff tables for escaped HTML, clarity, and visual polish. Confidence: medium. Status: considering.

## Static trial makers shuffle blocks unless ordered explicitly

The first participant recording showed rounds in the order 2, 1, 3, 4, 5 because
`StaticTrialMaker` inherits a randomized default `choose_block_order`. Repeated
game rounds should use explicit blocks plus a sorted block order when the visible
round sequence matters.

*Actions:*
- **PsyNetSkills:** Add a note to experiment implementation guidance that ordered repeated tasks need explicit block ordering or a timeline loop. Confidence: high. Status: considering.
