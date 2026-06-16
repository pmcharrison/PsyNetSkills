---
title: Integrate a JavaScript discovery game into an aggregated transmission chain
type: experiment implementation
difficulty: 9
authors: [pmcharrison]
---

Implement a PsyNet experiment that turns the JavaScript crystal-discovery game
from the `discovery-chains` reference repository into an aggregated transmission
chain experiment. The original game asks participants to move a rover around a
grid, pick up crystals, attempt fusions, harvest crystals for points, and write
messages for later participants. The PsyNet implementation should preserve the
participant-facing game mechanics and the intergenerational message logic while
using PsyNet's chain, node, trial, asset, and data-saving abstractions wherever
possible.

The target design is an aggregated chain rather than a one-participant-at-a-time
imitation chain. For each chain and condition, all participants in generation
`g` should complete the same game condition. Their scores and outgoing messages
should then be aggregated into the message set shown to participants in
generation `g + 1`. The implementation should make this aggregation explicit in
PsyNet data structures so that a reviewer can reconstruct which generation
produced each message set, which participant records contributed to it, and which
message set each later participant saw.

Use the supplied JavaScript game as the behavioral reference. Participants should
still be able to:

- read clear instructions for the crystal-harvesting task;
- move through the grid with the keyboard;
- pick up, fuse, drop, and harvest crystals;
- see current points, actions remaining, the carried crystal, the current tile,
  fusion hints, discovered recipes, and harvested rewards;
- encounter configurable fusion conditions corresponding to the original
  `easy`, `medium`, and `hard` rule families;
- write outgoing strategy and rule messages after completing the game; and
- in later generations, browse previous messages, save highlighted text into a
  notebook, write a short strategy summary, and carry that summary into the game.

The base generation should use the no-message game flow corresponding to
`task-base.html` and `task-base.js`. Later generations should use the
message-reading flow corresponding to `task-after.html`, `task-after.js`,
`selection.js`, and `messages.js`. The aggregation step should follow the intent
of `prepare_messages.py`: sample or select previous-generation messages within
condition using performance-sensitive weighting or ranking, then expose the
resulting structured message set to the next generation. Preserve enough
configuration hooks to change the sampling rule, sample size, number of chains,
conditions, generation count, and participants per generation without rewriting
the experiment architecture.

For local simulation and video evidence, configure a compact demonstration run
with exactly one chain, one condition, two participant trials per generation, and
three complete generations. This local configuration should demonstrate the full
logic:

1. generation 0 participants play the base game and submit outgoing messages;
2. the experiment aggregates generation 0 outputs into a message set;
3. generation 1 participants read the aggregated messages, save notebook notes,
   play the game, and submit new messages;
4. the experiment aggregates generation 1 outputs into the next message set; and
5. generation 2 participants receive the generation 1 message set and complete
   the same after-message flow.

Design the code so that the local demonstration configuration can be replaced by
the full specification from `desc.md`: 20 chains, three conditions (`easy`,
`medium`, `hard`), three generations per chain, and 20 participants per
generation. The full parameters should live in a single clear configuration
object or equivalent PsyNet settings layer; the local demonstration should be a
small parameter choice, not a separate experiment.

The implementation should save robust structured data. At minimum, save:

- chain id, condition, generation index, and participant/trial index within the
  generation;
- the exact game configuration used, including grid size, action budget, item
  definitions, transition rule, random seed or reproducible item layout where
  feasible, and regeneration setting;
- all game actions and events needed to reconstruct movement, pickups, fusions,
  drops, harvests, score changes, and game end;
- discovered transition records and harvested reward records;
- outgoing `messageHow` and `messageRules` text after sanitization;
- the incoming message set shown to each later-generation participant;
- notebook highlights, deleted notes, message dwell/read events, and strategy
  summary for later-generation participants;
- aggregation inputs, aggregation weights or ranks, selected messages, and the
  generated message payload passed to the next generation; and
- timing metadata for instruction, message browsing, reflection, game play, and
  message composition.

Avoid relying on the original PHP save endpoint or ad hoc browser downloads.
All participant responses, game events, aggregation records, and evidence needed
for analysis should be saved through PsyNet/Dallinger mechanisms. Free-text data
should be sanitized enough to avoid downstream parsing problems while preserving
the substantive content of participant messages.

Include a simulation or bot path that can complete the compact three-generation
demonstration without human intervention. The simulated participants should
exercise the real game and message logic rather than bypassing it entirely. It is
acceptable for bots to use deterministic movement/action scripts or a small test
mode that makes successful fusions reachable, provided that the same transition,
scoring, message, aggregation, and data-saving code paths run as in the browser
experiment.

Collect evidence from the compact local run. The attempt should include:

- a participant-facing video showing the game UI and the message-reading flow;
- terminal or log evidence that three generations completed for one chain with
  two participant trials per generation;
- evidence that generation 1 received aggregated messages from generation 0 and
  generation 2 received aggregated messages from generation 1;
- an exported local data artifact or concise inspection output demonstrating the
  saved chain, trial, message, and aggregation records; and
- a short implementation note explaining how to switch from the compact local
  configuration to the full `desc.md` parameter specification.

Do not configure real participant recruitment, production credentials, AWS,
Prolific, Cint, or external paid services. The challenge should be demonstrated
with local PsyNet execution, local simulated or bot participants, and local
exported data only.
