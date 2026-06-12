---
score: 7
---

# Evaluation

## Summary

The human evaluator rated the implementation 7/10. The experiment uses core PsyNet objects and the fixation-cross logic works well, but the visual presentation needs polish.

## Strengths

- The fixation cross logic seems to work well.
- The implementation uses core PsyNet objects.

## Weaknesses

- The fixation cross is a bit too large.
- The same/different question should appear below the stimulus display in a centered layout, rather than over the display.

## Criteria

- [x] Reaction time should be using javascript but in a minimal way. Specifically, the reaction time should be strongly tied to native events in the event management system in PsyNet, and js of reaction time measure should be isolated and minimal. Response should be recorded in the answer of each trial. If possible use existing reaction time mechanisms in PsyNet Control classes.
- [x] The request to allow keyboard buttons pressing should be implemented using KeyboardPushButtonControl which already implements this feature rather than by a dedicated js.
- [ ] First priority for correct display of all visual elements, with the right time, and no additional lingering display items such as fixation crosses or unrelated graphical elements that are not specified. Evaluator noted the fixation cross works but is a bit too large.
- [ ] Response buttons and questions should be centered around the stimuli. Evaluator noted the same/different question should appear below the stimulus display in a centered fashion, rather than over the display.
- [x] Do not show technical details that are not participant-facing (e.g., labeling the stimuli "stimuli" etc).
- [x] Make sure that PsyNet node and trial constructs were used correctly. There are two valid options:
  - Each node represents a pair of stimuli, and all 900 options are provided as nodes, in each trial participants are assigned to one of them by random.
  - Nodes represent the same/different conditions. In each trial the finalize_trial function is used to randomize on the fly.

## Notes

- Human evaluator feedback: "overall I would give this implementation 7/10. The fixation cross logic seems to work well, and the code uses core psynet objects. The presentation visuality could be improved, for instance the fixation cross is a bit too large, and the same or different question should not appear over the stimulus display but rather below it (in a centered fashion)."
