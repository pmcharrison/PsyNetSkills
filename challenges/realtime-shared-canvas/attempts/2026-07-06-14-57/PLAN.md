# Plan

## Methods

The experiment will be a real-time synchronous navigation task for small groups
of participants. Participants will first read instructions describing the shared
canvas, arrow-key controls, inertial movement, visible coins, real-time
co-presence, and the coin bonus rule. They will then wait in a synchronous
grouping stage until the configured number of participants is available. The
group size will be parameterized, with a default of two and validation that the
minimum group size is two.

Each group will enter one live navigation trial in one assigned world. A world
will be a square coordinate space with a fixed canvas size, a stable world id,
a reproducible random seed, and a list of coin positions generated for that
world. All participants in the group will see the same coins. Participants will
move their own avatar using the arrow keys. Movement will be continuous:
keyboard input will adjust acceleration or intended direction, velocity will be
integrated over time, friction will create modest inertia, and positions will be
clamped to the canvas bounds.

Participants will send their current position and velocity to the live session
every 50 ms. Each browser will render the canvas every 25 ms. Remote players
will be drawn from the most recent known position, velocity, and timestamp,
using linear interpolation or short-horizon extrapolation capped to avoid large
jumps. When a participant overlaps a coin, the browser will send a collection
message identifying the coin. The server-side live session reduction will accept
the first valid collection, remove that coin from the shared state, and add
`$0.10` to the collector's bonus. If two participants collect the same coin at
nearly the same time, later collection events for that coin will be ignored.

The trial will have a fixed duration so that the group cannot remain on the live
page indefinitely. The completion page will summarize the participant's collected
coins and resulting bonus. The exported data will allow reconstruction of group
membership, world assignment, coin positions, position updates, collection
events, and final bonuses.

## Implementation

The attempt will live under `code/realtime_shared_canvas/` so the experiment is
self-contained and avoids using the generic directory name `code` as an import
package. I will start from a minimal PsyNet experiment structure and add the
standard support files needed by local PsyNet checks.

The implementation will use PsyNet synchronous grouping and a `StaticTrialMaker`.
Static nodes will represent worlds. A helper will generate a small list of world
definitions at startup, each containing a world id, canvas dimensions, seed, coin
radius, and coin coordinates. A custom static trial class will build or retrieve
the live session for the participant's group and assigned world.

The real-time architecture will follow the public reference pattern:

- A generic `LiveEvent` table will persist live websocket messages.
- A generic `LiveSession` table will store the reduced shared session state.
- A generic `LiveSessionWebSocket` element will parse messages, create events,
  reduce non-skipped events, and broadcast session payloads.
- Shared-canvas-specific subclasses will extend the generic classes only for
  world initialization, player-state reduction, collection reduction, and
  tailored broadcast payloads.

Navigation updates will be represented as `PositionEvent` messages. Coin pickups
will be represented as `CollectEvent` messages. Both will use the generic live
event machinery so they share one websocket transport and one persisted event
stream. The reduced live session state will include participant ids, world
metadata, player states keyed by participant id, available coins, collected
coins, per-participant collection counts, and per-participant bonus totals.

The participant interface will be a custom JavaScript page rendered by PsyNet.
It will contain:

- A square canvas with the participant's own avatar, remote avatars, and all
  uncollected coins.
- A small bonus display showing the participant's current coin bonus, without a
  full status panel.
- Keyboard handlers for arrow-key input.
- One 25 ms rendering loop.
- One 50 ms websocket send loop for local position and velocity.
- Websocket message handlers that update the local cache of remote players,
  coins, and collection outcomes as messages arrive.

Bots and simulations will need to cover grouped participation. The first
implementation pass will provide deterministic bot behavior that waits through
the grouping pages and completes the trial. If browser-only websocket and canvas
code cannot be fully exercised by PsyNet bots, I will document that limitation
and use Playwright-based participant evidence after the plan is approved.

After implementation, the validation and evidence plan is:

- Run `python experiment.py` from the experiment directory.
- Run `psynet test local`.
- Run `psynet debug local` and collect participant-flow screenshots and
  `evidence/participant.mp4` using the participant-recording workflow.
- Run `psynet performance-test local` with JSON output under `evidence/`.
- Run `psynet simulate` and save `evidence/simulated_data.zip`.
- Write and execute `evidence/analyses/analysis.ipynb`, keeping it small enough
  for dashboard rendering.
- Write `REPORT.md` summarizing implementation, validation, evidence, and any
  limitations.

## Human review checkpoint

Implementation must pause here. After the human reviewer approves this plan, I
will continue with experiment code, simulation, analysis, evidence collection,
and the final report.
