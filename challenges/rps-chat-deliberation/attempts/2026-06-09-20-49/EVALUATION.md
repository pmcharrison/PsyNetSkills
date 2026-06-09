---
score:
---

# Evaluation

## Summary

Summarize the human evaluator's overall judgment.

## Strengths

- 

## Weaknesses

- 

## Criteria

- [ ] The implementation extends the `rock_paper_scissors` demo rather than replacing it with an unrelated experiment.
- [ ] Each rock-paper-scissors group enters a chat room immediately before the decision stage for that round, not only after gameplay or on a separate page unrelated to the upcoming choice.
- [ ] The chat room is associated with the same participant group that plays the subsequent rock-paper-scissors round; deliberation partners and game partners are identical.
- [ ] Participants can send and receive messages freely during the deliberation phase through a working chat interface.
- [ ] The deliberation phase lasts exactly 15 seconds and closes automatically for all group members without requiring manual advancement by participants.
- [ ] After the deliberation window ends, all grouped participants transition together into the rock-paper-scissors decision stage.
- [ ] The original rock-paper-scissors functionality after deliberation is preserved: synchronous choice, scoring, feedback, and post-round behavior from the base demo still work.
- [ ] Chat transcripts are stored in the experiment data.
- [ ] Saved data are sufficient to reconstruct participant group membership, chat-room membership, message timestamps, and the timing of transitions between chat and game phases.
- [ ] The deliberation pattern is implemented in a modular, reusable way rather than as a one-off hack tightly coupled to a single page template.
- [ ] The solution uses PsyNet-native grouping and chat patterns where appropriate, stays reasonably concise, and resembles other PsyNet demo experiments in structure and code size.
- [ ] The implementation relies on basic PsyNet functions and does not use too much frontend or JavaScript.
- [ ] The implementation does not contain almost any custom JavaScript, in the spirit of PsyNet demos where only core essential behavior is presented.

## Notes

- Score and feedback should come from a human evaluator, captured
  conversationally when working with Cursor Cloud Agents.
- Evidence includes a visual-only participant recording because this experiment
  has no participant-facing audio stimuli.
