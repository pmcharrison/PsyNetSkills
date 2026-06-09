---
score: 6
---

# Evaluation

## Summary

The evaluator scored the attempt 6/10. Functionally, the implementation works well and demonstrates the requested chat deliberation before rock-paper-scissors gameplay, but it adds too much custom code for a demo-style PsyNet solution. The main concern is that the attempt bends away from the "pure PsyNet", no-custom-JS style preferred for demos.

## Strengths

- The grouped chat deliberation, automatic transition, and preserved rock-paper-scissors gameplay are functionally successful.
- The attempt demonstrates the requested behavior clearly in participant evidence.

## Weaknesses

- The `record_deliberation_start` and `record_deliberation_release` helpers may be unnecessary relative to the original demo and add extra bookkeeping.
- The custom countdown JavaScript is useful, but it introduces too much custom script for the intended demo style.
- A simpler, more PsyNet-native solution would be preferable even if it bends the exact UX expectations slightly.

## Criteria

- [x] The implementation extends the `rock_paper_scissors` demo rather than replacing it with an unrelated experiment.
- [x] Each rock-paper-scissors group enters a chat room immediately before the decision stage for that round, not only after gameplay or on a separate page unrelated to the upcoming choice.
- [x] The chat room is associated with the same participant group that plays the subsequent rock-paper-scissors round; deliberation partners and game partners are identical.
- [x] Participants can send and receive messages freely during the deliberation phase through a working chat interface.
- [x] The deliberation phase lasts exactly one minute and closes automatically for all group members without requiring manual advancement by participants.
- [x] After the deliberation window ends, all grouped participants transition together into the rock-paper-scissors decision stage.
- [x] The original rock-paper-scissors functionality after deliberation is preserved: synchronous choice, scoring, feedback, and post-round behavior from the base demo still work.
- [x] Chat transcripts are stored in the experiment data.
- [x] Saved data are sufficient to reconstruct participant group membership, chat-room membership, message timestamps, and the timing of transitions between chat and game phases.
- [ ] The deliberation pattern is implemented in a modular, reusable way rather than as a one-off hack tightly coupled to a single page template. Functional, but too much custom countdown/bookkeeping code was added for a demo-style solution.
- [ ] The solution uses PsyNet-native grouping and chat patterns where appropriate, stays reasonably concise, and resembles other PsyNet demo experiments in structure and code size. It uses native grouping/chat, but the custom JavaScript and extra recording helpers make it less concise and less demo-like than desired.

## Notes

- Evaluator feedback: "Overall, you did a great job. However, I am not fully convinced by the use of record_deliberation_release and record_deliberation_start; I am not sure these elements are essential, and the original demo did not include them. I also did not like the addition of custom JavaScript for the countdown. I understand why this is a useful feature, but it introduces quite a lot of custom JS, which is not really in the spirit of PsyNet. While implementing this feature is legitimate in principle, in this case I think it would be better to avoid it in order to preserve the 'pure PsyNet,' no-custom-JS style that we try to maintain in the demos. So main weakness are the fact that too much custom code was added, functionally this is great but we should avoid so much custom script even if we bend a bit the use case, and what one can expect."
