---
title: Simple Visual Similarity Experiment
type: experiment implementation
difficulty: 4
authors: [raja-marjieh]
---

## Background

The experiment investigates explicit similarity judgments between simple visual stimuli. On each trial, participants view a pair of stimuli and rate how similar they appear.

## Stimuli

The stimulus set consists of colored circles with a fixed size. The implementation should allow additional dimensions, such as size, to be added later.

## Procedure

Each trial begins with a fixation cross.

The fixation is followed by a pair of stimuli presented simultaneously.

Participants rate the similarity of the two stimuli on a 5-point Likert scale, ranging from 1 = Completely Dissimilar to 5 = Completely Similar.

All stimulus pairs should be presented. For each trial, the exact stimulus pair, participant response, and reaction time are recorded.

Each participant completes 10 random trials.

## Implementation details

- Use psychophysics skills and other relevant skills available.
- Measure reaction time and store this information in every trial.
- Allow participants in the forced choice to respond by pressing a button on the keyboard.
- Include an analysis script or notebook that summarizes similarity ratings as a heatmap, and reaction times as average over pairs of stimuli from exported or simulated data.
