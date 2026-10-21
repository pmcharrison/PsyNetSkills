---
title: Real-time shared canvas navigation
type: experiment implementation
difficulty: 7
authors: [lucasgautheron]
---

Implement a PsyNet experiment in which groups of participants move freely within
a shared square canvas. Each participant controls one player avatar with the
left, right, up, and down arrow keys, and all participants can see the other
members of their group moving in real time. The shared world should also contain
randomly placed coins that participants can collect by moving over them.

## Procedure

Participants should first read concise instructions explaining the controls, the
shared canvas, the presence of other live participants, and the goal of the
demonstration. After any necessary consent and instruction pages, participants
should wait until enough active participants are available to form a group. The
group size should be controlled by a global experiment parameter and must allow
at least two participants.

Once a group has formed, all members should enter the same live navigation
trial. The canvas should be square, with dimensions controlled by a global
experiment parameter. Each participant should be assigned a stable display name,
color, or marker that remains consistent throughout the trial, and the
participant's own marker should be clearly distinguishable from the markers
representing other participants.

Participants should move continuously rather than jumping from cell to cell.
Arrow-key input should update acceleration or intended direction, and the player
state should include both position and velocity. Motion should include a modest
amount of inertia so that participants continue moving briefly after a key is
released and decelerate smoothly rather than stopping instantly. Movement should
remain bounded by the edges of the square canvas.

Each world should contain a set of visible coins. Coin positions should be
randomly generated as part of the world definition and should therefore be
specific to the assigned network or world, not regenerated independently for
each participant. All participants should see all currently available coins on
the canvas. When a participant moves over a coin, the coin should be collected,
removed from the shared world state, and increase that participant's bonus by
`$0.10`. The implementation should prevent the same coin from being collected
twice if two participants reach it at nearly the same time.

## Real-time state exchange

The experiment should send each participant's current position and velocity to
the live session every 50 ms. The client should refresh the rendered canvas every
25 ms. Rendering should use linear interpolation based on the most recent known
position, velocity, and timestamp for each player, so that other participants'
motion appears smooth even when websocket updates arrive at a lower frequency
than the drawing loop.

Incoming websocket data should be parsed as it arrives and used to update the
client's local cache of remote player states, available coins, and collected
coins. The client-side implementation should keep this flow clean: one loop for
drawing the canvas, one loop for sending the local participant's current
position and velocity, and event handlers for keyboard input, coin-collection
detection, and incoming websocket messages.

## Experiment structure

Use a `StaticTrialMaker` for now. The static nodes or trials should represent
different "worlds" that groups navigate. These worlds do not need to differ in
complex ways, but their initialization should be cleanly represented in trial or
node definitions. At minimum, each world definition should include its own coin
positions and any random seed or generation metadata needed to reproduce those
positions. Future implementations should be able to add world-specific terrain,
goals, obstacles, or other parameters without rewriting the real-time session
logic.

Participants should be grouped synchronously before entering a world. Each group
should complete one live navigation trial together. The implementation should
record the group membership, assigned world, participant labels or colors,
canvas parameters, timing parameters, coin positions, collection outcomes,
bonuses, and all live position-update events needed to reconstruct the
interaction.

## Implementation requirements

Base the live websocket architecture on the generic classes used in the
`adaptive-realtime-prisoners-dilemma` reference attempt. In particular:

- Use the same generic `LiveEvent`, `LiveSession`, and `LiveSessionWebSocket`
  approach for receiving messages, persisting live events, reducing session
  state, and broadcasting websocket payloads.
- Extend those generic classes only where the shared-canvas task requires
  world-specific state, player-state reduction, or tailored broadcast payloads.
- Represent navigation updates with a `PositionEvent` and coin pickups with a
  separate `CollectEvent`, using the generic live-event machinery rather than a
  parallel custom transport.
- Do not copy or implement the adaptive treatment-assignment logic from the
  Prisoner's Dilemma example; it is not relevant to this challenge.
- Keep the world assignment static, using `StaticTrialMaker`.
- Avoid production credentials or external services beyond local PsyNet
  development defaults.

## Interface

Build a polished participant interface centered on the shared square canvas. The
canvas should make the participant's own player visually distinct, show the
other participants' current interpolated positions, display all uncollected
coins, and remain responsive while websocket messages are being sent and
received. The interface should include a short status area showing the
participant's own position and velocity, the group size, the world identifier or
name, the participant's collected-coin count, and the current coin bonus.

The trial should have a clear duration or completion rule so participants do not
remain in the live canvas indefinitely. At the end of the trial, participants
should see a completion page confirming that the navigation session is finished
and summarizing their coin bonus.

## Evidence

Submitted evidence should demonstrate:

- At least two participants being grouped and released into the same canvas.
- The group-size parameter controlling how many participants share the world.
- Participants moving with arrow keys, with visible inertia and bounded motion.
- Other participants' positions updating smoothly in real time with little
  visible lag.
- Position and velocity updates being sent every 50 ms and canvas rendering
  running every 25 ms.
- Coins appearing at world-specific positions, being visible to all
  participants, disappearing after collection, and increasing the collector's
  bonus by `$0.10` per coin.
- `PositionEvent` and `CollectEvent` being persisted and reduced through the
  live-session architecture.
- The implementation using the generic live event, live session, and websocket
  architecture from the reference attempt.
- Static world assignment through `StaticTrialMaker`, with clean world
  initialization, including coin positions, suitable for future extension.
