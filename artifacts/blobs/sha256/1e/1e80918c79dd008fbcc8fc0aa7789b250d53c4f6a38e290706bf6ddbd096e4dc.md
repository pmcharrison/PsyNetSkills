# Real-time synchronous pixel game

The runnable PsyNet experiment is in `real_time_synchronous_game/`.

Key implementation points:

- `SimpleGrouper` forms groups, defaulting to 2 participants via `pixel_game_group_size`.
- `StaticTrialMaker` assigns one shared static trial to each sync group.
- `EnablePixelGame` registers the `pixel_game` websocket channel.
- The server persists game sessions, raw click events, public state deliveries, and private state deliveries.
- Websocket messages broadcast only public state. Private rewards and per-click bonuses are fetched through `/pixel_game_private_state` with the participant id and `unique_id`.

For short visual evidence, run with `PSYNET_PROFILE=minimal`; this keeps the default canonical 64-round configuration in `config.txt` but uses 4 rounds when the profile is active.
