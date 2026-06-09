---
title: Ferry market Unity game
type: experiment implementation
difficulty: 5
authors: [ofer]
---

Implement a PsyNet experiment where participants provide informed consent, read
brief instructions, play the Ferry Market Unity game as a WebGL app, and
complete the experiment after finishing the game.

## Procedure

Participants should first see an informed consent page. They should be able to
confirm consent before continuing, and participants who do not consent should
not proceed into the game.

After consent, participants should see a welcome or instruction page explaining
that they will play a Unity-based game called Ferry Market. The instructions
should tell participants how to start the game, how to interact with it, and
that the experiment will continue only after the game reports that it is
finished.

After the instructions, participants should enter the Unity game. The provided
Unity build should run as a WebGL app embedded in the PsyNet participant flow.
Participants should be able to play the game without needing to leave the
experiment context or perform any manual setup beyond ordinary browser
interaction.

When the participant finishes the game, the PsyNet experiment should detect the
completion event and advance to a short final page. The final page should thank
the participant and clearly indicate that the task is complete.

## Data and implementation

Use PsyNet's standard dashboard and experiment metadata only. Do not require any
custom participant-level data beyond what PsyNet already records for ordinary
page progression, timing, and completion status.

The implementation should be simple to run locally with PsyNet. Include clear
setup instructions for where to place or serve the provided Unity WebGL build,
and keep the integration self-contained so that future challenge attempts can be
evaluated without external credentials or private services.

The submitted evidence should demonstrate that an automated test participant can
interact with the WebGL game by clicking the relevant in-game buttons or objects,
finish the Unity task, and advance through the final PsyNet completion page.
