---
title: Ferry market Unity game
type: experiment implementation
difficulty: 5
authors: [ofer]
---

Implement a PsyNet experiment where participants read brief instructions, play
the Ferry Market Unity game, and complete the experiment after finishing the
game.

## Procedure

Participants should first see a welcome or instruction page explaining that they
will play a Unity-based game called Ferry Market. The instructions should tell
participants how to start the game, how to interact with it, and that the
experiment will continue only after the game reports that it is finished.

After the instructions, participants should enter the Unity game. The game should
be embedded or launched in a way that fits naturally within the PsyNet
participant flow. Participants should be able to play the game without needing
to leave the experiment context or perform any manual setup beyond ordinary
browser interaction.

When the participant finishes the game, the PsyNet experiment should detect the
completion event and advance to a short final page. The final page should thank
the participant and clearly indicate that the task is complete.

## Data and implementation

Use PsyNet's standard dashboard and experiment metadata only. Do not require any
custom participant-level data beyond what PsyNet already records for ordinary
page progression, timing, and completion status.

The implementation should be simple to run locally with PsyNet. If the Unity
game needs static build files, include clear setup instructions and keep the
integration self-contained so that future challenge attempts can be evaluated
without external credentials or private services.
