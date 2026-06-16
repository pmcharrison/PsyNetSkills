# Report

## Summary

This attempt implements a self-contained PsyNet experiment that adapts the public `discovery-chains` crystal-discovery game into an aggregated transmission chain. The compact local configuration uses one chain, the `easy` rule family, two participant trials per generation, and three participant-facing generations. The same configuration object also records the full design target: 20 chains, `easy`/`medium`/`hard` conditions, three generations, and 20 participants per generation.

## Implementation

The experiment lives in `code/discovery_game/`. PsyNet owns the transmission-chain state through `DiscoveryChainNode`, `DiscoveryTrial`, and `ChainTrialMaker` with `trials_per_node=2`, `max_nodes_per_chain=3`, `chain_type="across"`, and `wait_for_networks=True`. Generation 0 receives an empty message set. When a generation reaches two finalized trials, `DiscoveryChainNode.make_next_definition()` aggregates the completed trial answers, computes log-points weights and ranks, stores the aggregation audit in the node variables, and passes the selected message payload in the next node definition.

The browser game is implemented as a custom PsyNet page that vendors the upstream `discovery-chains` HTML, JavaScript, CSS, and image assets under `static/discovery-chains/`. Generation 0 renders a template generated from upstream `task-base.html`; later generations render a template generated from upstream `task-after.html`. The page loads the upstream `utilities.js`, `grid.js`, `selection.js`, `task-base.js`, and `task-after.js` files, while small PsyNet adapter scripts provide trial-definition input, dynamic incoming messages, corrected static asset paths, and `psynet.nextPage(...)` submission. The original PHP save endpoint is not used; all data are submitted as the PsyNet trial answer.

## Configuration

The compact and full parameter sets live in `RUN_CONFIGS` in `experiment.py`. To switch from the compact evidence run to the full `desc.md` design, change `ACTIVE_CONFIG_NAME` from `"compact"` to `"full"`. No architecture changes are needed; the start nodes, chain count, conditions, participants per generation, and aggregation settings are all derived from that object.

## Validation and evidence

- `python experiment.py` imports successfully.
- `psynet test local` passes with six bots and checks that generations 0, 1, and 2 each have two trials, generation 1 receives generation 0 messages, generation 2 receives generation 1 messages, and aggregation variables exist on chain nodes.
- `psynet simulate` passes and exports `evidence/simulated_data.zip`.
- `evidence/aggregation_inspection.txt` shows six trials, two per generation, with generation 1 receiving two messages from generation 0 and generation 2 receiving two messages from generation 1.
- `evidence/analyses/analysis.ipynb` reads the simulated export directly, asserts the generation/message flow, summarizes aggregation audit records, and plots deterministic bot rewards.
- `evidence/performance.json` records a 40-bot, five-minute local performance test with zero bot errors and zero request errors.
- `evidence/participant.mp4` and `evidence/screenshots/` document the participant-facing flow, including aggregated messages, notebook saving, strategy summary, game interaction, and outgoing message composition.
- `evidence/monitor.html` stores a local dashboard snapshot.

## Limitations

The compact run uses deterministic bot behavior and a deterministic layout that makes successful same-shape fusions reachable. These artifacts validate workflow, data paths, aggregation, and UI behavior; they should not be interpreted as human behavioral results. Human author metadata remains pending in `agent.json` until the reviewer provides the GitHub username to credit.
