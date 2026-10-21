---
title: Visual Psychophysics Battery
type: experiment implementation
difficulty: 5
authors: [raja-marjieh]
---

Implement a PsyNet experiment that combines the following three existing challenges into a single visual psychophysics battery. Each experiment should become an experimental block in accordance with core PsyNet objects.

## Block 1: Simple visual discrimination experiment

### Background

The experiment used a classical two-alternative forced-choice same–different task. On each trial, participants viewed a pair of stimuli and indicated whether the two stimuli were the same or different by pressing the corresponding response key.

### Stimuli

The stimulus set consisted of 30 simple colors, each presented as a colored circle with about 1/4 of the presentation display.

### Procedure

1. Each trial began with a fixation cross presented for 500 ms. 
2. The fixation was followed by two colored circles displayed simultaneously for 1000 ms. 
3. On the same trials, the two circles had identical colors; on different trials, they had different colors. Stimulus pairs were sampled randomly on each trial. 
4. After stimulus offset, a blank display was presented for 500 ms.
5. Next a two-alternative response appears asking participants to indicate whether the stimuli were the same or different.
6. Participants complete a set of 10 trials each.

## Block 2: Simple Visual Similarity Experiment

### Background

The experiment investigates explicit similarity judgments between simple visual stimuli. On each trial, participants view a pair of stimuli and rate how similar they appear.

### Stimuli

Same as block 1.

### Procedure

Each trial begins with a fixation cross.

The fixation is followed by a pair of stimuli presented simultaneously.

Participants rate the similarity of the two stimuli on a 5-point Likert scale, ranging from 1 = Completely Dissimilar to 5 = Completely Similar.

All stimulus pairs should be presented. For each trial, the exact stimulus pair, participant response, and reaction time are recorded.

Each participant completes 10 random trials.

## Block 3: Simple Multi-Item Identification Experiment

### Background

The experiment investigates multi-item identification from briefly presented visual arrays. On each trial, participants view a numbered set of stimuli, followed by a probe, and identify which item from the original set is identical or most similar to the probe.

### Stimuli

Same as block 1.

### Procedure

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

Include an analysis script or jupyter notebook display that summarizes performance across the different conditions, as well as reaction times from exported or simulated data. Add a side-by-side visualization of the three empirical matrices (e.g. using plt.matshow) derived from each block based on simulated data (Block 1: count the number of times each pair of colors was labeled as same (normalized by the overall number of trials), Block 2: average similarity score per pair divided by 5 so that it varies between 0 and 1, and Block 3: number of times a stimulus was selected in response to a given probe (normalized by the total number of trials). Have the three subplots share the same color bar. In the simulation, you can use a simple probabilistic choice model where the similarity or confusion probabilities between two stimuli x and y is proportional to exp(-d(x,y)) where d is their hue distance on the color circle.
