---
title: Adaptive musical preference experiment
type: experiment implementation
difficulty: 8
authors: [pmcharrison]
---

Implement a PsyNet experiment that estimates a participant's preference over a
small space of musical stimuli using adaptive pairwise choices.

The experiment should:

- Define a stimulus space with at least two interpretable dimensions, such as
  tempo and brightness.
- Present pairs of stimuli to the participant and ask which they prefer.
- Use earlier choices to influence at least some later pairings.
- Save enough metadata to reconstruct the sequence of pairs and choices.
- Include a short post-task summary page for the participant.
- Include an analysis script or notebook that summarizes the collected choices
  from exported or simulated data.

It is acceptable to synthesize simple audio stimuli rather than using real music
recordings, provided the generated stimuli clearly vary along the declared
dimensions.
