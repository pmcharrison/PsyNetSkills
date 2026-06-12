# Plan details: Primary color rating experiment

This file is the authoritative specification for the experiment. Implementation must match it exactly; `PLAN.md` is the human-readable summary rendered on the dashboard. Keep the two in sync — on conflict, fix the conflict at review rather than letting the implementation drift.

## Section status

| Section | Status |
|---|---|
| Science | out of scope (simple technical implementation challenge; no new science claim) |
| Method | under review |
| Implementation | under review |

- **Mode:** challenge attempt.
- **Source / canonical reference:** none; public challenge instructions in `challenge/INSTRUCTIONS.md`.

## Science decisions

| Decision | Choice | Status |
|---|---|---|
| Research question framing | Technical validation of a three-color PsyNet rating task, not a new scientific color-preference study. | under review |
| Hypotheses / expected patterns | No scientific hypothesis; expected validation pattern is one saved 1-7 pleasantness rating for each required color. | under review |
| Stimulus domain and source | Fixed primary-color stimuli: red `#ff0000`, green `#00ff00`, and blue `#0000ff`, generated in HTML/CSS rather than loaded from external assets. | under review |
| Participant population | Local PsyNet bots and any manual local browser tester; production participant population is outside scope. | under review |
| Interpretation boundary | Local evidence can prove implementation correctness and data capture only; it cannot support population claims about color pleasantness. | under review |

## Method decisions

| Decision | Choice | Status |
|---|---|---|
| Within vs. between participants | Within participant: every participant rates red, green, and blue once. | under review |
| Trial structure (static vs. chain/network) | Simple fixed static-trial structure with `StaticTrialMaker`; no chain, network, node progression, grouping, or adaptive allocation. | under review |
| Synchronous structure (none / grouped / realtime) | None; participants complete independent trials asynchronously. | under review |
| AI involvement (none / stimulus generation / participant / hybrid) | None; no AI stimulus generation, evaluator, or participant role. | under review |
| Sample size and rationale | Local validation uses PsyNet bots and manual/browser checks; no production sample size is specified for this technical demo. | under review |
| Prescreens and quality controls | No prescreen, comprehension check, attention check, or practice phase; the simple rating task uses required responses and standard PsyNet completion handling. | under review |
| Primary analysis | Verify exported data contains one rating per color per participant; optional descriptive summaries may report counts and mean rating by color. | under review |

## Implementation specification

Implement the attempt under `challenges/primary-color-rating/attempts/2026-06-12-12-57/code/primary_color_rating/` so all runnable code is self-contained in the attempt directory and avoids importing from sibling attempts. The experiment directory will include the standard files required for a minimal PsyNet local launch, including `experiment.py`, `config.txt`, `.gitignore`, and any test files needed for participant-flow evidence.

Use PsyNet `13.3.0a0` from the refreshed checkout at `~/PsyNet` commit `d84382b300c4d4cc8a0b0648428152e0740ab7d2`. The closest base demo is `~/PsyNet/demos/experiments/simple_audio_rating/experiment.py` for the `StaticTrial`, `StaticNode`, `StaticTrialMaker`, `ModularPage`, and rating-control structure; `~/PsyNet/demos/experiments/hello_world/experiment.py` is the reference for short `InfoPage` welcome/thanks pages. The implementation must not use external service credentials, production recruiters, external color assets, or custom JavaScript unless native PsyNet controls cannot render the required swatch.

`experiment.py` should define a color manifest in code or a committed small manifest with exactly these records, in this order: `{"color_name": "red", "hex_color": "#ff0000", "display_order": 1}`, `{"color_name": "green", "hex_color": "#00ff00", "display_order": 2}`, and `{"color_name": "blue", "hex_color": "#0000ff", "display_order": 3}`. A helper such as `get_nodes()` should convert that manifest to `StaticNode` definitions. A custom `ColorRatingTrial(StaticTrial)` should render a `ModularPage` whose prompt includes the color name, the exact question "How pleasant is this color?", and a large visible swatch styled with the node's `hex_color`. The response control should be PsyNet's `RatingControl(values=7, min_description="Not at all pleasant", max_description="Very pleasant")` or the closest native PsyNet equivalent that saves a single scalar rating. Trial `time_estimate` can be about 5-10 seconds.

The `Exp` class should set a clear label such as "Primary color rating" and use a `Timeline` containing: a short welcome `InfoPage`; a `StaticTrialMaker(id_="color_rating", trial_class=ColorRatingTrial, nodes=get_nodes, expected_trials_per_participant="n_nodes", max_trials_per_participant="n_nodes")`; and a short thank-you `InfoPage`. `config.txt` should use local generic recruiter defaults only and a short task title/description suitable for local testing.

The data contract is one completed PsyNet trial per color per participant. The node definition must expose `color_name`, `hex_color`, and `display_order`; the trial answer must contain exactly one 1-7 pleasantness rating, with no combined multi-rating answer needed. Browser and bot evidence should be able to verify that all three colors appear and that completed data can be grouped by `color_name`.

Bots should submit valid ratings for all three static trials. A deterministic bot path is preferred for evidence reproducibility, such as cycling valid ratings or choosing a fixed midpoint, while preserving framework-created bot compatibility. If a custom `run_bot` is added, it must support `bot=None` and delegate to `super().run_bot(...)` for framework-created bots so `psynet performance-test local` can run.

Testing and evidence after plan approval should include these checks where the environment permits: `python experiment.py` to list or validate the three-color manifest; `psynet test local` from the experiment directory; Playwright-driven participant-flow screenshots showing welcome, a representative color-rating trial, and thank-you; `evidence/participant.mp4` only if video adds useful review value beyond screenshots; `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output /workspace/challenges/primary-color-rating/attempts/2026-06-12-12-57/evidence/performance.json`; a PsyNet monitor snapshot at `evidence/monitor.html`; and exported data at `evidence/data.zip` using an absolute output path under the attempt's `evidence/` directory. Any unavailable command or service should be recorded in `TIMELINE.md` and `EVALUATION.md` as a blocker.

| Decision | Choice | Status |
|---|---|---|
| Base demo | `simple_audio_rating` static rating architecture, simplified for visual color swatches; `hello_world` for minimal info pages. | under review |
| Experiment architecture | Static-trial PsyNet experiment with three fixed `StaticNode` definitions and one custom `StaticTrial`. | under review |
| Data schema highlights | Node definition: `color_name`, `hex_color`, `display_order`; trial answer: one scalar 1-7 pleasantness rating. | under review |
| Testing and evidence plan | Run manifest check, `psynet test local`, participant-flow screenshots/video if useful, performance JSON, monitor snapshot, and export data zip. | under review |

## Decision log

- 2026-06-12 — purpose inference: chose simple implementation / technical demo over a new science question or replication because the public challenge asks for a minimal locally runnable PsyNet experiment and gives no research hypothesis or source study; inferred from challenge instructions.
- 2026-06-12 — fixed trial order: chose red, green, then blue over randomization or counterbalancing because the public instruction says to show each primary color "in turn" and fixed order makes the required one-rating-per-color evidence direct; default, overridable at review.
- 2026-06-12 — trial architecture: chose `StaticTrialMaker` over a hand-written sequence of pages or chain/network architecture because the task needs repeated independent trials with saved trial records but no evolving state, allocation network, or participant interaction; inferred from challenge instructions and the simple-round-structure checklist.
- 2026-06-12 — response control: chose a native PsyNet `RatingControl` over custom JavaScript or a slider because the required 1-7 discrete pleasantness scale maps directly to a built-in rating control and should save a single scalar answer; default, overridable at review.
