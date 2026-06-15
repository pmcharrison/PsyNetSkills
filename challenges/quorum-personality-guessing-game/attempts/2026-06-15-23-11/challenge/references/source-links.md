# Source links

This challenge is based on two user-provided sources:

- PsyNet synchronization tutorial, "Quorum" section:
  <https://psynetdev.gitlab.io/PsyNet/tutorials/synchronization.html#quorum>
- Ultimatum-game `PersonalityTrial` source:
  <https://github.com/EAndrade-Lotero/ultimatum_game/blob/main/big_five.py>

The quorum tutorial demonstrates a `SimpleGrouper` with `waiting_logic`,
`join_existing_groups`, `min_group_size`, `max_wait_time`, and a `trial_maker`
custom wrapper that lets participants complete waiting trials while the quorum
forms.

The `PersonalityTrial` source loads short Big Five items from
`static/big_five_short.csv`, formats each item into the sentence stem
"I see myself as someone who ...", and uses a five-point accuracy scale from
"Very inaccurate" to "Very accurate".
