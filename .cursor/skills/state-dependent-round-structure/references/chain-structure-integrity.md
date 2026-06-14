# Chain structure integrity

Use this reference when a PsyNet chain experiment requires a visible round,
game, exchange, or iteration to correspond to a `ChainNode`.

## Success invariant

Define the expected mapping before running bots:

- `expected_rounds`: the number of visible rounds that should become chain
  state.
- `expected_trials_per_node`: the number of completed participant trials needed
  to summarize one node, usually `ChainTrialMaker.trials_per_node`.
- `trial_maker_id`: the chain trial maker under review.

After a bot run, compare expected rounds to distinct trial-attached nodes:

- `len({trial.node_id for trial in completed_trials}) == expected_rounds`
- `len(completed_trials) == expected_rounds * expected_trials_per_node`
- every completed trial is a `ChainTrial` subclass attached to the expected
  `trial_maker_id`;
- every trial answer contains the fields consumed by `ChainNode.summarize_trials`;
- child node definitions contain the state generated from the previous node's
  completed trials.

Do not require the raw node table count to equal `expected_rounds`. PsyNet can
hold extra seed, queued, or unserved nodes. The safer graph check is the number
of distinct node ids used by completed trials.

## Bot check template

Add this kind of assertion to `Experiment.test_check_bot` or
`Experiment.test_check_bots` after `psynet test local` completes the participant
flow:

```python
completed_trials = GameTrial.query.filter_by(failed=False).all()
trial_node_ids = {trial.node_id for trial in completed_trials}

assert len(trial_node_ids) == EXPECTED_ROUNDS
assert len(completed_trials) == EXPECTED_ROUNDS * EXPECTED_TRIALS_PER_NODE
assert all(isinstance(trial, GameTrial) for trial in completed_trials)
assert {trial.trial_maker_id for trial in completed_trials} == {
    "expected_trial_maker_id"
}
assert all(isinstance(trial.node, GameNode) for trial in completed_trials)
```

For grouped games, add per-node checks:

```python
trials_by_node = {}
for trial in completed_trials:
    trials_by_node.setdefault(trial.node_id, []).append(trial)

assert all(
    len(trials) == EXPECTED_TRIALS_PER_NODE
    for trials in trials_by_node.values()
)
```

When the answer stores an internal round counter, assert it agrees with the
node graph. A mismatch such as `max(answer["counted_rounds"]) == 3` with only
one distinct `trial.node_id` means the UI completed three rounds inside a single
chain node.

## What the ultimatum comparison showed

The working ultimatum implementation used:

- `expected_trials_per_participant=NUMBER_OF_ROUNDS`
- `max_trials_per_participant=NUMBER_OF_ROUNDS`
- `max_nodes_per_chain=NUMBER_OF_ROUNDS`
- `trials_per_node=2`

With two bots and `NUMBER_OF_ROUNDS = 25`, the topology probe generated:

- `trials=50`
- `distinct_trial_nodes=25`
- `trials_per_node=2`
- `nodes=26`

The extra raw node row did not violate the round mapping because 25 distinct
nodes were actually used by completed trials.

The failing ultimatum attempt used:

- `expected_trials_per_participant=1`
- `max_trials_per_participant=1`
- `max_nodes_per_chain=1`
- `trials_per_node=2`

With two bots and `ROUNDS_REQUIRED = 3`, the generated data showed:

- `trials=2`
- `distinct_trial_nodes=1`
- `max(answer["counted_rounds"])=3`
- `trials_per_node=2`

That structure is wrong for a spec requiring one chain node per round: the game
completed three visible rounds inside one `ChainTrial`, so downstream chain
state could not advance round by round.

## Code smells that cause the wrong structure

- `expected_trials_per_participant`, `max_trials_per_participant`, or
  `max_nodes_per_chain` is set to `1` while the participant UI loops through
  many visible rounds.
- A `ChainTrial.show_trial` contains an internal round loop or websocket session
  that saves only one final answer, but the spec expects each round to become
  node state.
- `ChainNode.summarize_trials` receives one final session transcript instead of
  one completed trial set per round.
- Bot assertions check only participant variables or final answer counters and
  never count distinct `trial.node_id` values.
- The dashboard shows plausible completion counts, but the network graph has a
  single trial-attached node for multiple visible rounds.

## Interpreting valid exceptions

Multiple trials per node are valid when `trials_per_node > 1` intentionally
collects several participant responses before advancing. A single trial can also
contain multiple browser pages or phases. Flag the structure only when the
experiment specification says each visible round should be chain state and the
bot-generated trial graph does not show one trial-attached node per round.
