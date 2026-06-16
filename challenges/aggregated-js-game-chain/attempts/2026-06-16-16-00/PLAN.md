# Plan

## Science

This experiment will implement an aggregated transmission-chain version of the JavaScript crystal-discovery game. The central behavioral question is how strategy and rule knowledge transmitted by a previous generation changes later participants' exploration, fusion discoveries, harvesting rewards, and outgoing advice. The compact local configuration will be treated as a technical demonstration rather than evidence about human behavior: one chain, the `easy` condition, two participants per generation, and three generations. The full configuration will expose the same architecture with 20 chains, the `easy`, `medium`, and `hard` rule families, three generations per chain, and 20 participants per generation.

## Methods

Participants will play a grid-based crystal-harvesting game adapted from the public `discovery-chains` reference repository at commit `b89fcf85a475a8757f4d0bac6238edbb2ba43ca3`. Each participant controls a rover on a 15 x 15 grid with a configurable action budget, initially 40 actions. The participant can move with the arrow keys, pick up a crystal with the spacebar, fuse a carried crystal with a crystal on the current tile, harvest a carried crystal on an empty tile for points, or drop the carried crystal with the `D` key. Crystals vary by shape, texture, and level. Level determines reward magnitude, and the fusion rule family (`easy`, `medium`, or `hard`) determines which pairs produce a higher-level crystal.

Generation 0 will complete the base no-message game flow. Participants will read task instructions, play the game, and write two outgoing messages: one about useful strategies and one about inferred fusion rules. Later generations will complete an after-message flow. They will browse a structured set of messages aggregated from the previous generation, open individual message cards, save highlighted text into a notebook, write a short strategy summary, play the same game condition, and then write outgoing strategy and rule messages for the next generation.

For each chain and condition, participants in generation `g` will all receive the same current node definition. After the configured number of participants for that generation have completed and their trials have been processed, the experiment will aggregate their scores and outgoing messages into the message payload for generation `g + 1`. The aggregation will follow the intent of `prepare_messages.py`: sanitize free text, compute a performance-sensitive weight from total points using `log1p(total_points)`, rank or sample messages within condition, and store the selected structured messages with contributor trial identifiers. The compact run will use a deterministic seed and sample size small enough that two participants per generation can demonstrate the complete pipeline.

The saved dataset will allow reviewers to reconstruct the chain id, condition, generation, trial index within generation, game configuration, participant game events, discovered transitions, harvested rewards, outgoing messages, incoming message payload, message browsing events, notebook highlights and deletions, strategy summary, aggregation inputs, aggregation weights or ranks, selected messages, and timing metadata.

## Implementation

The experiment will live under `code/discovery_game/` so Dallinger does not import a top-level package named `code`. The implementation will use PsyNet's chain framework rather than a one-participant imitation-chain template. A single configuration object will define the run parameters:

- `chains`: compact `1`, full `20`;
- `conditions`: compact `['easy']`, full `['easy', 'medium', 'hard']`;
- `generations`: `3`;
- `participants_per_generation`: compact `2`, full `20`;
- `message_sample_size`, `aggregation_rule`, `random_seed`, `grid_size`, `action_budget`, `allow_regeneration`, and the rule-family mapping.

A custom `DiscoveryChainNode` will subclass `psynet.trial.chain.ChainNode`. The starting node definition will include the chain id, condition, generation index `0`, game seed/layout specification, action budget, rule family, and an empty incoming message set. `make_next_definition()` will read `self.completed_and_processed_trials`, extract each trial's structured answer, compute the aggregation, write aggregation audit metadata to `self.var` or the child definition, and return the child node definition for the next generation. The child definition will include `generation_index = self.degree + 1`, the selected incoming message set, contributor trial ids, aggregation seed, ranks or weights, and the same game configuration so later participants play the same condition.

A custom `DiscoveryTrial` will subclass `psynet.trial.chain.ChainTrial`. Its `show_trial()` method will choose the base or after-message front-end from the trial definition: generation 0 will render the base game flow, and generation 1+ will render the message-browsing and reflection flow before the game. The JavaScript game code will remain self-contained in static files as far as possible. PsyNet will construct and pass a serialized trial definition into the browser layer, replacing the original global random condition assignment and PHP save endpoint. The front end will submit one structured PsyNet answer containing game events, actions, transition discoveries, reward harvests, outgoing message text, incoming message metadata, notebook events, strategy summary, and timing fields.

The trial maker will use `psynet.trial.chain.ChainTrialMaker` with `chain_type='across'`, `start_nodes` generated for each configured `(chain_id, condition)`, `trials_per_node=participants_per_generation`, `max_nodes_per_chain=generations`, `balance_across_chains=True`, `wait_for_networks=True`, `recruit_mode='n_trials'`, and no real recruiter or production service configuration. This uses PsyNet's built-in head-node growth gate so generation `g + 1` is unavailable until generation `g` has the configured number of completed and processed trials.

For browser behavior, the implementation will adapt the original `task-base.html`, `task-after.html`, `task-base.js`, `task-after.js`, `grid.js`, `selection.js`, `messages.js`, `config.js`, and `utilities.js` into a PsyNet template/static structure with source attribution. Necessary changes will be limited to receiving the PsyNet trial definition, using deterministic seeded item layouts in local evidence runs, emitting structured answers through PsyNet, and exposing bot hooks for deterministic participant simulation. The original PHP save path and ad hoc downloads will not be used.

Bots will exercise the real trial-answer path. A deterministic compact profile will read at least one incoming message in later generations, save a notebook highlight, write a strategy summary, perform a small scripted sequence of movement, pickup, fusion, harvest, and drop actions, and submit non-empty outgoing strategy and rule messages. The bot path may use a deterministic, evidence-only layout seed that puts successful fusions within reach, but it must use the same transition, scoring, message, aggregation, and PsyNet data-saving code paths as the browser experiment.

Validation after implementation will include `python experiment.py`, `psynet test local`, `psynet simulate` with enough bots to complete the three-generation compact run, an exported `evidence/simulated_data.zip`, a headless executed `evidence/analyses/analysis.ipynb`, `psynet performance-test local` with JSON output, and participant-flow evidence created with the repository's participant-video workflow. The evidence inspection will explicitly show that generation 1 received aggregation from generation 0 and generation 2 received aggregation from generation 1.

## Review questions

- Is it acceptable for the compact local evidence run to use the `easy` rule family as its single condition, while keeping `medium` and `hard` available through the shared configuration object?
- Should aggregation select all messages in the compact two-participant generation, or should it still sample/rank down to a smaller fixed message set to mirror the full-run behavior?
- Should aggregation audit records be stored only in PsyNet node/trial variables, or should the implementation also add a dedicated SQL table with one row per aggregation event for easier export review?
