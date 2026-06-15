---
title: Simple Multi-Item Identification Experiment
type: experiment implementation
difficulty: 4
authors: [raja-marjieh]
---

## Background

The experiment investigates multi-item identification from briefly presented visual arrays. On each trial, participants view a numbered set of stimuli, followed by a probe, and identify which item from the original set is identical or most similar to the probe.

## Stimuli

The stimulus set consists of colored circles with a fixed size. The implementation should allow additional dimensions, such as size, to be added later. On each trial, a set of N stimuli is presented, where N can be 3, 4, or 5.

## Procedure

Each trial begins with a fixation cross.

The fixation is followed by N numbered stimuli arranged around the fixation cross.

The stimulus array is presented for a fixed duration and then disappears.

After a blank delay of at least 500 ms, a single probe stimulus is presented.

The probe may either be part of the original stimulus set or a new stimulus that was not presented in the set.

Participants identify the number of the item from the original set that is identical to, or most similar to, the probe.

For probes that were part of the original set, the correct response is the matching item number. For probes that were not part of the set, the selected response should be recorded as a similarity-based generalization choice.

For each trial, record the full stimulus set, item numbers, item positions, probe identity, probe condition, participant response, accuracy where applicable, and reaction time.

Each participant completes 10 random trials, sampled across set sizes N = 3, 4, and 5 and across probe conditions.

## Implementation details

Use psychophysics skills and other relevant skills available.

Measure reaction time and store this information in every trial.

Allow participants to respond by pressing a button on the keyboard, while still enabling mouse clicks.

Include an analysis script or notebook that summarizes identification accuracy, generalization choices, confusion probabilities across stimuli, and reaction times from exported or simulated data.
