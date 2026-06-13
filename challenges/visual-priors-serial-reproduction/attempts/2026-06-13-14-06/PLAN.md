# Plan

## Science

The experiment will recreate the participant-facing serial reproduction method from Langlois, Jacoby, Suchow, and Griffiths (2017). The scientific target is not a full-scale data collection with hundreds of seeds, but a faithful runnable PsyNet implementation that demonstrates how spatial-memory responses can be passed down chains. Each trial presents a dot inside a geometric outline, removes the dot after a brief exposure, then asks the participant to reproduce the remembered location. Across chain generations, each participant's reproduced location becomes the dot location shown to the next participant, allowing repeated memory distortions to reveal shape-dependent visual priors.

## Methods

Participants will complete an instruction phase, practice trials, and experimental serial reproduction trials. Practice will use a circle with ten random dot locations. Each practice stimulus will show a 400 px shape outline and a small black dot for 4000 ms, followed by a 1000 ms blank retention interval, and then a response screen where the participant clicks inside the same outline. A visible dot will appear at the clicked location, and the participant may reclick before submitting.

Experimental trials will use the core shapes described in Experiment 1: circle, equilateral triangle, square, vertical oval, horizontal oval, and regular pentagon. Each experimental stimulus will show for 1000 ms, followed by the same 1000 ms retention interval and click-to-reproduce response. The outline will be placed with small randomized offsets within a larger response area so that participants cannot rely purely on absolute screen coordinates. Responses will be stored as normalized shape-local coordinates, making each reproduction portable across later randomized outline positions.

The serial reproduction design will use multiple chains per shape. A chain begins from a random seed point sampled inside the corresponding shape. The response from generation N will provide the seed shown to generation N + 1. Chains will run for ten generations when enough participants or bots are available. In local testing and simulation, the number of chains will be reduced enough to keep evidence generation practical while still exercising all shapes and several chain transitions.

Trial feedback will compare the reproduced and target coordinates. If both absolute x and y errors are within 8% of the shape's width and height, the trial will show green "This was accurate" feedback; otherwise it will show red "This was not accurate" feedback. The implementation will record this accuracy flag for analysis. Bonus payment behavior will not be wired to a real payment service; the feedback is the relevant participant-facing requirement for a local challenge attempt.

## Implementation

The experiment will live under `code/visual_priors_serial_reproduction/` to avoid importing a Python package named `code`. It will be built as a self-contained PsyNet experiment with standard support files copied from a current PsyNet demo, then adapted rather than depending on repository files outside the attempt directory.

The main experiment will define:

- Shape geometry helpers for drawing SVG outlines and testing whether normalized points fall inside each shape.
- Seed-generation helpers that sample valid normalized points inside each shape.
- A custom serial reproduction trial class that stores `shape`, `chain_id`, `generation`, `target_x`, `target_y`, `response_x`, `response_y`, `error_x`, `error_y`, and `accurate`.
- A custom page sequence for stimulus display, retention interval, response collection, and feedback.
- A chain maker or network-style trial maker that assigns each participant to available chain nodes and routes each submitted response into the next generation's stimulus.
- Bot support that can complete practice and experimental trials with small noisy responses around the target, preserving the serial reproduction mechanism during `psynet test local`, `psynet simulate`, and performance checks.

The participant UI will use inline SVG or HTML canvas inside PsyNet pages. SVG is preferred because it keeps shape rendering, target dots, response dots, and click coordinate conversion explicit and testable. The client script will convert click positions to normalized shape-local coordinates, reject clicks outside the current shape when possible, and enable submit only after a valid response. If PsyNet's built-in controls make repeated clicks awkward, a small custom page class will be used.

The analysis notebook will read the simulated export directly from `evidence/simulated_data.zip`, reconstruct the chain table, and summarize the experiment by shape and generation. It will plot normalized response positions over the outline for several shapes, report accuracy rates, and compute simple convergence summaries such as generation-to-generation displacement and distance from the final generation. If sufficient simulated data exist, it will include kernel density visualizations for the final generations.

Validation after implementation will include:

- `python experiment.py` from the experiment directory.
- `psynet test local` to exercise launch and bot completion.
- `psynet simulate` with enough bots to produce a usable chain export saved as `evidence/simulated_data.zip`.
- The canonical `evidence/analyses/analysis.ipynb` with visible code, tables, plots, and interpretation.
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output <attempt>/evidence/performance.json`, unless local services block performance testing.
- Participant-flow evidence with a short browser recording and targeted screenshots showing stimulus, retention, response, and feedback states.

Implementation should continue only after human review confirms this plan.
