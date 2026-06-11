---
title: Simple visual discrimination experiment
type: experiment implementation
difficulty: 4
authors: [raja-marjieh]
---

## Background

The experiment used a classical two-alternative forced-choice same–different task. On each trial, participants viewed a pair of stimuli and indicated whether the two stimuli were the same or different by pressing the corresponding response key.

## Stimuli

The stimulus set consisted of 30 simple colors, each presented as a colored circle with about 1/4 of the presentation display.

## Procedure

1. Each trial began with a fixation cross presented for 500 ms. 
2. The fixation was followed by two colored circles displayed simultaneously for 1000 ms. 
3. On the same trials, the two circles had identical colors; on different trials, they had different colors. Stimulus pairs were sampled randomly on each trial. 
4. After stimulus offset, a blank screen was presented for 500 ms.
5. Next a two-alternative response asking participants to indicate whether the stimuli were the same or different.
6. Participants complete a set of 10 trials each.

## Implementation details

1. Measure reaction time and store this information for every trial.
2. Allow participants in the forced choice to respond by pressing a button on keyboard.

## Additional details

Use record-participant-video skills in addition to the following additional remark:

Make systematic use of tests: testing experiment logic with psynet test local, testing front-end logic with Playwright, and testing visual logic with video testing. When video testing, make sure to be efficient, e.g. by running the experiment in a ‘minimal’ mode with a small number of trials; long videos are time-consuming to create and to analyze.
