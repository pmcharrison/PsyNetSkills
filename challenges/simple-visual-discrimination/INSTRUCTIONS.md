---
title: Simple visual discrimination experiment
type: experiment implementation
difficulty: 4
authors: [raja-marjieh]
---

--Background
The experiment used a classical two-alternative forced-choice same–different task. On each trial, participants viewed a pair of stimuli and indicated whether the two stimuli were the same or different by pressing the corresponding response key.

--Stimuli
The stimulus set consisted of 30 simple colors, each presented as a colored circle with about 1/4 of the presentation display.

--Procedure
1. Each trial began with a fixation cross presented for 500 ms. 
2. The fixation was followed by two colored circles displayed simultaneously for 1000 ms. 
3. On the same trials, the two circles had identical colors; on different trials, they had different colors. Stimulus pairs were sampled randomly on each trial. 
4. After stimulus offset, a blank screen was presented for 500 ms.
5. Next a two-alternative response asking participants to indicate whether the stimuli were the same or different.
6. Participants complete a set of 10 trials each.
7. At the end, participants complete an Ishihara color blindness test, their results are recorded but the participants are not failed. This is followed by a simple demographics survey collecting age, gender, and mother tongue.

Implementation details:
1. Measure reaction time and store this information for every trial.
2. Allow participants in the forced choice to respond by pressing a button on keyboard.

--Evaluation
Reaction time should be using javascript but in a minimal way. Specifically, the reaction time should be strongly tied to native events in the event management system in PsyNet, and js of reaction time measure should be isolated and minimal. Response should be recorded in the answer of each trial. If possible use existing reaction time mechanisms in PsyNet Control classes.

The request to allow keyboard buttons pressing should be implemented using KeyboardPushButtonControl which already implements this feature rather than by a dedicated js.

First priority for correct display of all visual elements, with the right time, and no additional lingering display items such as fixation crosses or unrelated graphical elements that are not specified.

Response buttons and questions should be centered around the stimuli.

Do not show technical details that are not participant-facing (e.g., labeling the stimuli “stimuli” etc).

Make sure that PsyNet node and trial constructs were used correctly. There are two valid options:
a. Each node represents a pair of stimuli, and all 900 options are provided as nodes, in each trial participants are assigned to one of them by random. 
b. Nodes represent the same/different conditions. In each trial the finalize_trial function is used to randomize on the fly.
