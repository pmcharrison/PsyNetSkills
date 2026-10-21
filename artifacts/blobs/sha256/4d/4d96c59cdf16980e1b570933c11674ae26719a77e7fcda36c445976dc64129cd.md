Reaction time should be measured using JavaScript only in a minimal and isolated way. Reaction-time measurement should be closely tied to native events in PsyNet’s event-management system. Where possible, existing reaction-time mechanisms in PsyNet Control classes should be used.

The highest priority is the correct display of all visual elements with the specified timing. No additional or lingering display elements should appear, including fixation crosses, previous stimuli, or unrelated graphical components not specified in the design.

Response buttons and questions should be centered relative to the stimuli.

Participant-facing displays should not include technical labels or implementation-related text, such as labeling the visual items as “stimuli.”

Make sure that PsyNet nodes and trial constructs are used correctly. Nodes may represent individual stimulus pairs, or pairs may be generated within finalize_definition, provided that the design ensures all required pairs are presented and recorded.

Make sure keyboard mapping occurs only in the similarity judgment phase, and keyboard strokes are mapped correctly while still enabling mouse clicks. Implementation should use native psynet elements like KeyboardPushButtonControl  as much as possible.
