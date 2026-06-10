# Reference materials

## Source experiment

The target behaviour is a music-domain reimplementation of the rolling-inventory
replication experiment in the Computational Audition Lab GitLab repository:

https://gitlab.com/computational-audition-lab/niche-lucas/-/tree/rolling-inventory-replication

The reference branch implements a collective drawing task in which participants
maintain a rolling market inventory of binary grid images. Each round has an
adoption step (select a market item) followed by a creation step (edit or create
a new item). The implementation uses PsyNet imitation chains with custom
`GridNode` inventory logic in `experiment.py`.

Implementers with access to the workshop GitLab token should read that branch
directly and preserve all non-domain experiment logic unless the challenge
instructions explicitly call for a music-specific change.

The melody version should intentionally omit the drawing experiment's mouse
movement tracking, stroke event tracking, and other drawing-specific interaction
logs.

## Creation interface sketch

The music creation interface should resemble the attached step-sequencer mock-up:

- Three pitch rows labelled **Mi**, **Re**, and **Do** (top to bottom).
- Nine time slots labelled **1** through **9**.
- One active note per time slot at most.
- Colour coding: Mi = red, Re = green, Do = blue.
- A **Play melody** control that previews the current sequence before submission.

## Market preview

During adoption, market items should be previewed primarily through audio
playback. Showing the underlying note grid is not required. A waveform display
is optional but encouraged if it can be implemented cleanly.

Before the main task begins, participants should complete a short audio
pre-screening step that confirms they can play and hear experiment audio.
