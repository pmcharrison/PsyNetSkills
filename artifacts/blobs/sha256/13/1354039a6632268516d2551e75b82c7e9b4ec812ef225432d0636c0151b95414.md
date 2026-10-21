# Evaluation criteria

Use these criteria to assess completed attempts for the chat deliberation on
rock–paper–scissors challenge.

An attempt should pass only if it demonstrates all of the following:

- The implementation extends the `rock_paper_scissors` demo rather than replacing
  it with an unrelated experiment.
- Each rock–paper–scissors group enters a chat room immediately before the
  decision stage for that round, not only after gameplay or on a separate page
  unrelated to the upcoming choice.
- The chat room is associated with the same participant group that plays the
  subsequent rock–paper–scissors round; deliberation partners and game partners
  are identical.
- Participants can send and receive messages freely during the deliberation
  phase through a working chat interface.
- The deliberation phase lasts exactly one minute and closes automatically for
  all group members without requiring manual advancement by participants.
- After the deliberation window ends, all grouped participants transition
  together into the rock–paper–scissors decision stage.
- The original rock–paper–scissors functionality after deliberation is
  preserved: synchronous choice, scoring, feedback, and post-round behavior
  from the base demo still work.
- Chat transcripts are stored in the experiment data.
- Saved data are sufficient to reconstruct participant group membership,
  chat-room membership, message timestamps, and the timing of transitions
  between chat and game phases.
- The deliberation pattern is implemented in a modular, reusable way rather
  than as a one-off hack tightly coupled to a single page template.
- The solution uses PsyNet-native grouping and chat patterns where appropriate,
  stays reasonably concise, and resembles other PsyNet demo experiments in
  structure and code size.

Common reasons to fail an attempt:

- Chat happens after the game choice instead of before it.
- Deliberation partners differ from the participants who play together.
- The one-minute limit is approximate, participant-controlled, or implemented
  only as instructional text without enforced timing.
- Chat messages are not persisted or cannot be reconstructed from saved data.
- The rock–paper–scissors game logic is broken or substantially altered after
  the deliberation phase.
- The implementation reimplements low-level chat infrastructure when PsyNet's
  native chatroom support would suffice.
- The code is unnecessarily large, brittle, or not structured for reuse in
  other multi-participant experiments.
