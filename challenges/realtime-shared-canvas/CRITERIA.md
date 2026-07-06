Evaluation should check that:

- Participants can see each other move in real time, with very little visible
  lag.
- The implementation uses the generic classes for live events, live sessions,
  and websockets from the referenced approach.
- The experiment uses `StaticTrialMaker` to assign worlds to groups.
- World initialization is cleanly organized and easy to extend.
- The client-side code is elegant, with one loop to update the canvas every
  25 ms, one loop to send the current position and velocity every 50 ms, and
  separate parsing of incoming data as it arrives.
