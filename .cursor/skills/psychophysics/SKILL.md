---
name: psychophysics
description: Implement psychophysics experiments with PsyNet, focusing on precise visual displays, timing, response collection, and conservative interpretation of reference figures.
authors: [raja-marjieh]
---

# Implement PsyNet psychophysics experiment

## General guidelines

Follow the general workflow in `psynet-experiment-implementation/SKILL.md`.

- Prioritize correct display of all visual elements, correct timing, and no
  additional lingering display items such as fixation crosses or unrelated
  graphical elements that are not specified.

- Do not display any additional elements that are not mentioned in the task
  description.

- Make sure that PsyNet node and trial constructs are used correctly.

- Measure reaction time with JavaScript only when needed, and keep it minimal.
  Reaction time should be strongly tied to native events in PsyNet's event
  management system, and reaction-time JavaScript should be isolated. Responses
  should be recorded in the answer of each trial. Prefer existing PsyNet Control
  mechanisms where possible, for example `GraphicPrompt` frame sequencing with
  `prevent_control_response`/`activate_control_response`,
  `KeyboardPushButtonControl`, and event-log reaction-time extraction before
  adding custom JavaScript.

- Implement keyboard-button responses with `KeyboardPushButtonControl` rather
  than dedicated JavaScript.

- Center response buttons and questions around the stimuli.

- Do not show technical details that are not participant-facing, such as labeling
  display items "stimuli".

- When implementing an experiment based on a PDF paper, keep in mind that display
  items such as dots and stimuli may be exaggerated in size in schematic figures.
  If the paper provides explicit size specifications for the elements, use those
  values. If not, be cautious when estimating sizes from schematic figures,
  especially when the figure contains multiple components and the actual display
  is only one part of the image. However, if a screenshot or a clear
  single-display schematic is provided, the relative sizes are likely to be more
  indicative of the intended appearance.
