---
title: Visual priors serial reproduction
type: experiment implementation
difficulty: 9
authors: [pmcharrison]
---

Implement a PsyNet experiment that recreates the spatial-memory serial
reproduction study described by Langlois, Jacoby, Suchow, and Griffiths (2017),
"Uncovering visual priors in spatial memory using serial reproduction." The
source paper is provided in references/.

The experiment should implement the participant-facing procedure as a real
serial reproduction task. Participants view a small black dot inside a geometric
outline, remember its location after a delay, and then reproduce the dot by
clicking inside the same shape. The response from one participant becomes the
stimulus for the next participant in the chain.
