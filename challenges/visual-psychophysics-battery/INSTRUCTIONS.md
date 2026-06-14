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

### Implementation details

1. Use psychophysics skill for guidlines for implementation.
2. Measure reaction time and store this information for every trial.
3. Allow participants in the forced choice to respond by pressing a buttons on keyboard.

## Block 2: Simple Visual Similarity Experiment

### Background

The experiment investigates explicit similarity judgments between simple visual stimuli. On each trial, participants view a pair of stimuli and rate how similar they appear.

### Stimuli

The stimulus set consists of colored circles with a fixed size. The implementation should allow additional dimensions, such as size, to be added later.

### Procedure

Each trial begins with a fixation cross.

The fixation is followed by a pair of stimuli presented simultaneously.

Participants rate the similarity of the two stimuli on a 5-point Likert scale, ranging from 1 = Completely Dissimilar to 5 = Completely Similar.

All stimulus pairs should be presented. For each trial, the exact stimulus pair, participant response, and reaction time are recorded.

Each participant completes 10 random trials.

### Implementation details

- Use psychophysics skills and other relevant skills available.
- Measure reaction time and store this information in every trial.
- Allow participants in the forced choice to respond by pressing a button on the keyboard.
- Include an analysis script or notebook that summarizes similarity ratings as a heatmap, and reaction times as average over pairs of stimuli from exported or simulated data.

## Block 3: Simple Multi-Item Identification Experiment

### Background

The experiment investigates multi-item identification from briefly presented visual arrays. On each trial, participants view a numbered set of stimuli, followed by a probe, and identify which item from the original set is identical or most similar to the probe.

### Stimuli

The stimulus set consists of colored circles with a fixed size. The implementation should allow additional dimensions, such as size, to be added later. On each trial, a set of N stimuli is presented, where N can be 3, 4, or 5.

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

### Implementation details

Use psychophysics skills and other relevant skills available.

Measure reaction time and store this information in every trial.

Allow participants to respond by pressing a button on the keyboard, while still enabling mouse clicks.

Include an analysis script or notebook that summarizes identification accuracy, generalization choices, confusion probabilities across stimuli, and reaction times from exported or simulated data.
