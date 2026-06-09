---
title: Chat deliberation on rock–paper–scissors
type: feature integration
difficulty: 4
authors: [jacobyn]
---

Extend the PsyNet `rock_paper_scissors` demo by integrating chat functionality
in the style of the `chatrooms` demo. The goal is to let grouped participants
deliberate together for a fixed period immediately before each rock–paper–scissors
decision, then continue into the existing synchronous game flow unchanged.

## Procedure

After participants are grouped for rock–paper–scissors play, each group should
enter a dedicated chat room before making their choices. The chat room must be
tied to the same participant group that will play the subsequent game round.
Participants should be able to send and receive messages freely through the chat
interface while deliberation is open.

The deliberation phase should last 15 seconds. When that time elapses,
the chat phase should close automatically for all participants in the group, and
everyone should transition together into the rock–paper–scissors decision stage.
Participants who deliberated together must be the same participants who play
together in the immediately following game phase.

After deliberation ends, preserve the original rock–paper–scissors demo
behavior: synchronous choice, scoring, feedback, and any post-round interaction
already present in the base demo should continue to work as before.

## Data and implementation

Store chat transcripts as part of the experiment data. Save enough metadata to
reconstruct participant group membership, chat-room membership, timestamps for
all messages, and the timing of transitions between the chat and game phases.

Implement the solution in a reusable, modular way so the same deliberation
pattern could be dropped into other multi-participant PsyNet experiments with
minimal changes. Prefer PsyNet's native chat and grouping APIs over bespoke
infrastructure. Keep the codebase small, clean, and consistent with other PsyNet
demo experiments.

## Starting points

Use the existing PsyNet demos as references:

- `demos/experiments/rock_paper_scissors`
- `demos/experiments/chatrooms`

The submitted evidence should demonstrate grouped participants chatting during
the one-minute deliberation window, an automatic transition into the game phase,
and preserved rock–paper–scissors gameplay afterward.
