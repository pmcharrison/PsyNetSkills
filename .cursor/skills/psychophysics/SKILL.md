---
name: psychophysics
description: Design and validate PsyNet psychophysics experiments.
authors: [raja-marjieh]
---

# Psychophysics

## General guidelines

Follow general guidelines in psynet-experiment-implementation skills.

-- First priority for correct display of all visual elements, with the right time, and no additional lingering display items such as fixation crosses or unrelated graphical elements that are not specified.

-- Do not display any additional elements that are not mentioned in the task description.

-- Make sure that PsyNet node and trial constructs were used correctly.

-- Reaction time should be using javascript but in a minimal way. Specifically, the reaction time should be strongly tied to native events in the event management system in PsyNet, and js of reaction time measure should be isolated and minimal. Response should be recorded in the answer of each trial. If possible use existing reaction time mechanisms in PsyNet Control classes. For example prefer `GraphicPrompt` frame sequencing with `prevent_control_response`/`activate_control_response`, `KeyboardPushButtonControl`, and event-log reaction-time extraction before adding custom JavaScript.

-- Requests to allow keyboard buttons pressing should be implemented using KeyboardPushButtonControl which already implements this feature rather than by a dedicated js.

-- Response buttons and questions should be centered around the stimuli.

-- Do not show technical details that are not participant-facing (e.g., labeling the stimuli “stimuli” etc).

-- When implementing an experiment based on a PDF paper, keep in mind that display items such as dots and stimuli may be exaggerated in size in schematic figures. If the paper provides explicit size specifications for the elements, use those values. If not, be cautious when estimating sizes from schematic figures, especially when the figure contains multiple components and the actual display is only one part of the image. However, if a screenshot or a clear single-display schematic is provided, the relative sizes are likely to be more indicative of the intended appearance.
