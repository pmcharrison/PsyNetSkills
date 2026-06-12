---
name: psychophysics
description: Design and validate PsyNet psychophysics experiments.
authors: [raja-marjieh]
---


## General Guidelines
Follow general guidelines in psynet-experiment-implementation skills.

Reaction time should be using javascript but in a minimal way. Specifically, the reaction time should be strongly tied to native events in the event management system in PsyNet, and js of reaction time measure should be isolated and minimal. Response should be recorded in the answer of each trial. If possible use existing reaction time mechanisms in PsyNet Control classes.

Requests to allow keyboard buttons pressing should be implemented using KeyboardPushButtonControl which already implements this feature rather than by a dedicated js.

First priority for correct display of all visual elements, with the right time, and no additional lingering display items such as fixation crosses or unrelated graphical elements that are not specified.

For simple timed visual discrimination tasks, prefer `GraphicPrompt` frame sequencing with `prevent_control_response`/`activate_control_response`, `KeyboardPushButtonControl`, and event-log reaction-time extraction before adding custom JavaScript.

Response buttons and questions should be centered around the stimuli.

Do not show technical details that are not participant-facing (e.g., labeling the stimuli “stimuli” etc).

Make sure that PsyNet node and trial constructs were used correctly.
