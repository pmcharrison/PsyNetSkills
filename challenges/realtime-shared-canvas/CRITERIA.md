Evaluation should check that:

- Participants can see each other move in real time, with very little visible
  lag.
- The implementation uses the generic classes for live events, live sessions,
  and websockets from the referenced approach.
- The experiment uses `StaticTrialMaker` to assign worlds to groups.
- World initialization is cleanly organized and easy to extend.
- Coin positions are randomly generated per world or network, visible to all
  participants, and reproducible from the world definition.
- Coin collection uses a `CollectEvent` in addition to the `PositionEvent` used
  for navigation, removes collected coins from the shared state, and awards the
  collector `$0.10` per coin without double-counting races.
- The client-side code is elegant, with one loop to update the canvas every
  25 ms, one loop to send the current position and velocity every 50 ms, and
  separate parsing of incoming data as it arrives.
