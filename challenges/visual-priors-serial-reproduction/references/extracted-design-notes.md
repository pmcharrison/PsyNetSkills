# Extracted design notes

Source: Langlois, Jacoby, Suchow, and Griffiths (2017), "Uncovering visual
priors in spatial memory using serial reproduction."

These notes summarize implementation-relevant details from the supplied paper
excerpt. Attempt authors should still treat the paper PDF as the source of truth.

## Task

Participants remember the position of a small black dot inside a geometric
outline and reproduce the dot's location from memory. The task uses serial
reproduction: the response from one participant becomes the dot stimulus for the
next participant in the same chain.

## Stimuli

- Images are approximately 400 x 400 px.
- Each shape is a 6 px black outline on a white background.
- Experiment 1 uses six shapes: circle, equilateral triangle, square, vertical
  oval, horizontal oval, and regular pentagon.
- Experiment 2 repeats the same logic with regular polygons containing more than
  five vertices.
- Initial dots are sampled within shape boundaries. The paper reports 400 seeds
  for the circle and 500 seeds for each other Experiment 1 shape.
- The shape's position is randomized inside a larger canvas on experimental
  trials, to discourage participants from using absolute screen coordinates.

## Procedure

- Participants complete 10 practice trials with a circle.
- Practice trials show the dot for 4000 ms, followed by a blank screen for
  1000 ms, then the outline without the dot until response.
- Participants click to place the remembered dot location, may reposition the dot
  as needed, and confirm when done.
- Participants then complete 95 experimental trials with exactly one assigned
  shape.
- Experimental trials show the dot for 1000 ms and otherwise use the same
  response workflow as practice trials.
- The paper reports 10 serial reproduction iterations for each chain.

## Feedback and propagation

- Participants receive trial-by-trial accuracy feedback.
- Responses within 8% of the displayed shape's width and height are marked
  accurate with green feedback, "This was accurate", and receive bonus metadata.
- Responses outside this criterion are marked inaccurate with red feedback,
  "This was not accurate", receive no trial bonus, and are discarded from the
  experiment.
- Participants cannot provide multiple responses within a chain.

## Analysis targets

- Reconstruct each chain by shape, seed, and generation.
- Visualize response clouds across generations.
- Estimate final-generation priors with two-dimensional kernel density
  estimation.
- Compute convergence measures between generations, such as Jensen-Shannon
  divergence.
