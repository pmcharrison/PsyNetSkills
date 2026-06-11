## Evaluation

Reaction time should be using javascript but in a minimal way. Specifically, the reaction time should be strongly tied to native events in the event management system in PsyNet, and js of reaction time measure should be isolated and minimal. Response should be recorded in the answer of each trial. If possible use existing reaction time mechanisms in PsyNet Control classes.

The request to allow keyboard buttons pressing should be implemented using KeyboardPushButtonControl which already implements this feature rather than by a dedicated js.

First priority for correct display of all visual elements, with the right time, and no additional lingering display items such as fixation crosses or unrelated graphical elements that are not specified.

Response buttons and questions should be centered around the stimuli.

Do not show technical details that are not participant-facing (e.g., labeling the stimuli “stimuli” etc).

Make sure that PsyNet node and trial constructs were used correctly. There are two valid options:
a. Each node represents a pair of stimuli, and all 900 options are provided as nodes, in each trial participants are assigned to one of them by random. 
b. Nodes represent the same/different conditions. In each trial the finalize_trial function is used to randomize on the fly.
