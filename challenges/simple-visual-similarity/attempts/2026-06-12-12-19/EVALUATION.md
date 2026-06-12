---
score: 7
---

# Evaluation

## Summary

The experiment itself looks very good: the visual presentation is strong and the functionality appears to work well. The score is 7 because the implementation code is less satisfying, mainly due to code inconsistencies around custom JavaScript/CSS and reaction-time handling.

## Strengths

- Visual presentation is strong.
- Participant-facing functionality appears to work well.
- Timing solution is clever and efficient.
- Node and stimulus structure is well designed.

## Weaknesses

- The implementation relies substantially on explicit JavaScript and CSS where PsyNet's Graphics/Raphael system was expected and would likely have been the better fit.
- `format_answer` assigns an arbitrary fallback reaction time of `1.25` when no reaction-time data are available; inventing data in place of missing values is bad practice and potentially dangerous.
- The psychophysics skill did not sufficiently steer the implementation toward PsyNet Graphics for this simple visual-display task.

## Criteria

- [ ] Reaction time should be measured using JavaScript only in a minimal and isolated way. Reaction-time measurement should be closely tied to native events in PsyNet’s event-management system. Where possible, existing reaction-time mechanisms in PsyNet Control classes should be used. The implementation ties timing to event logs, but the arbitrary fallback reaction time violates the spirit of this criterion.
- [x] The highest priority is the correct display of all visual elements with the specified timing. No additional or lingering display elements should appear, including fixation crosses, previous stimuli, or unrelated graphical components not specified in the design.
- [x] Response buttons and questions should be centered relative to the stimuli.
- [x] Participant-facing displays should not include technical labels or implementation-related text, such as labeling the visual items as “stimuli.”
- [x] Make sure that PsyNet nodes and trial constructs are used correctly. Nodes may represent individual stimulus pairs, or pairs may be generated within finalize_definition, provided that the design ensures all required pairs are presented and recorded.
- [ ] Make sure keyboard mapping occurs only in the similarity judgment phase, and keyboard strokes are mapped correctly while still enabling mouse clicks. Implementation should use native psynet elements like KeyboardPushButtonControl as much as possible. Keyboard and mouse functionality work, but the implementation uses more custom JavaScript/CSS than expected.

## Notes

- Human evaluator score: 7/10.
- Human feedback emphasized that the experiment and functionality are strong, but the code should have used PsyNet Graphics/Raphael more directly and should not have imputed missing reaction-time values.
