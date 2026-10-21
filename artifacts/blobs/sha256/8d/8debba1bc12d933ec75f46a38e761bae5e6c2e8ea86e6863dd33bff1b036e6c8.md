---
title: Similarity, discrimination, and identification experiment
type: experiment implementation
difficulty: 5
authors: [raja-marjieh]
---

Implement a PsyNet experiment investigating how perceptual similarity judgments
relate to same-different discrimination and confusion probabilities in
multi-item identification.

The experiment should use simple visual stimuli, such as filled circles, that
vary along at least one perceptual dimension. The initial implementation should
use color as the primary dimension, while keeping the stimulus representation
and trial metadata extensible enough to add additional dimensions later, such as
size.

The experiment should include the following blocks. Each trial in every block
should begin with a fixation cross. Presentation and delay durations should be
fixed within the experiment, and all delays should last at least 500 ms.

## Same-different discrimination block

Participants should see two simultaneously presented stimuli and make a 2AFC
judgment indicating whether the stimuli are identical or different.

The block should:

- Include both identical and different stimulus pairs.
- Present trials in a randomized or otherwise documented order.
- Record the presented stimulus identities, stimulus attributes, participant
  response, accuracy, and reaction time for every trial.

## Similarity judgment block

Participants should rate the similarity of all stimulus pairs on a 7-point
Likert scale, where 0 means "Completely Dissimilar" and 6 means "Completely
Similar".

The block should:

- Present all relevant unordered stimulus pairs from the stimulus set, including
  identical pairs if they are useful as scale anchors.
- Use clear participant-facing labels for the endpoints of the scale.
- Record the pair identity, full stimulus metadata, rating, and reaction time
  for every trial.

## Multi-item identification block

Participants should view a display containing a set of numbered stimuli
arranged around a central fixation cross. The set size should vary across trials
with N = 3, 4, and 5. After a fixed presentation duration and a fixed delay of at
least 500 ms, participants should see a probe stimulus. The probe may either be
one of the stimuli from the preceding display or a lure that was not in the
display. Participants should select the number of the display item that is most
similar to the probe.

The block should:

- Balance or otherwise document the sampling of set sizes, display positions,
  probe-present trials, and probe-absent lure trials.
- Store the numbered display items, their positions, the probe stimulus, whether
  the probe was present in the display, the intended correct or nearest item,
  the participant response, accuracy or nearest-neighbor correctness, and
  reaction time.
- Save enough metadata to reconstruct the visual display shown on each trial.

## End-of-experiment measures

At the end of the experiment, administer:

- An Ishihara color-vision test.
- A demographics questionnaire.

## Analysis

Include an analysis script or notebook that can run on exported data or on a
documented simulated dataset. The analysis should summarize:

- Similarity judgments, including a stimulus-by-stimulus similarity matrix.
- Same-different discrimination performance and reaction times.
- Multi-item identification confusion probabilities by stimulus, set size, and
  probe-present versus probe-absent condition.
- Reaction time distributions for all task blocks.

The analysis should be documented well enough that a reviewer can understand how
trial-level records are transformed into the reported summaries.
