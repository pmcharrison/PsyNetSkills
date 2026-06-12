# Experiment plan: Primary color rating experiment

| Section | Status |
|---|---|
| Science | out of scope (simple technical demo requested by challenge) |
| Method | under review |
| Implementation | under review |

- **Purpose:** Simple implementation / technical demo — success means a runnable local PsyNet experiment presents red, green, and blue as separate trials and stores one 1-7 pleasantness rating per color.
- **Mode:** Challenge attempt.
- **Source / canonical reference:** `challenge/INSTRUCTIONS.md`.

## Science

This challenge is scoped as a simple implementation rather than a new scientific study or replication. The experiment will demonstrate a participant-facing PsyNet flow for collecting color pleasantness ratings, but it will not claim to estimate population-level color preferences, cultural differences, perceptual mechanisms, or causal effects. Any observed ratings from local bots or local test participants should be treated as technical validation data only.

### Key decisions

| Decision | Choice | Status |
|---|---|---|
| Research question framing | Out of scope; technical collection of pleasantness ratings only. | Inferred from challenge instructions |
| Hypotheses / expected patterns | None specified; no confirmatory hypothesis will be tested. | Inferred from challenge instructions |
| Stimulus domain and source | Three built-in primary color definitions: red, green, and blue. | Inferred from challenge instructions |
| Participant population | Local PsyNet test participants and bots for validation. | Default for challenge implementation |
| Interpretation boundary | Ratings demonstrate data capture, not a validated psychophysical or preference result. | Default for technical demo |

## Method

In brief, each participant will see a short welcome page, complete three color-rating trials, and then see a short thank-you page. The design is within participant: every participant rates red, green, and blue once. Each trial displays a single color swatch and asks, "How pleasant is this color?" with a 1-7 response scale. The primary output is one saved pleasantness rating per color.

The experiment uses a fixed static-trial design. Colors are not generated from participant responses, assigned to different groups, or linked across participants, so no chain, network, synchronous grouping, or real-time interaction is needed. Trial order may remain deterministic red, green, blue to keep the implementation transparent, or be randomized with a fixed static node set if review prefers order balancing; the recommended default is deterministic order because the public instructions emphasize simplicity rather than inference.

Participants will not complete demographics, device prescreening, comprehension checks, practice trials, post-experiment questionnaires, bonus calculations, or recruiter redirects. Those stages are outside this challenge's scope. The only quality control is native required response validation on the rating control so a participant cannot submit a trial without selecting a rating. There is no feedback about correctness because the task is subjective.

The planned analysis is a simple data integrity check: confirm each completed participant has exactly three trial records, one each for red, green, and blue, and that every rating is an integer from 1 to 7. If exploratory summaries are needed after implementation, they should report ratings by color without inferential claims.

### Key decisions

| Decision | Choice | Status |
|---|---|---|
| Within vs. between participants | Within participant; every participant rates all three colors once. | Inferred from challenge instructions |
| Trial structure (static vs. chain/network) | Static trials from a fixed manifest; no node evolution or participant allocation logic beyond `StaticTrialMaker`. | Inferred from challenge instructions and simple-round checklist |
| Synchronous structure (none / grouped / realtime) | None. Participants act independently. | Inferred from challenge instructions |
| AI involvement (none / stimulus generation / participant / hybrid) | None. | Inferred from challenge instructions |
| Sample size and rationale | Local validation size only; enough bots or manual runs to verify all three colors save ratings. | Default for technical demo |
| Prescreens and quality controls | No prescreens; required rating response per trial. | Default for simple subjective task |
| Primary analysis | Integrity check for one 1-7 rating per color per completed participant. | Default for technical demo |

## Implementation

- Put runnable experiment code under `code/primary_color_rating/` to avoid importing a package named `code`.
- Adapt the current PsyNet static-rating pattern from `~/PsyNet/demos/experiments/simple_audio_rating/experiment.py`.
- Define a small color manifest in `experiment.py`, for example red `[0, 100, 50]`, green `[120, 100, 50]`, and blue `[240, 100, 50]` in the HSL format expected by `ColorPrompt`.
- Represent each color as a `StaticNode` with `definition` fields such as `color_name` and `hsl`.
- Implement a `StaticTrial` subclass whose `show_trial` returns a `ModularPage` containing `ColorPrompt` and `RatingControl(values=7, min_description="Not at all pleasant", max_description="Very pleasant")`.
- Use `StaticTrialMaker` with `expected_trials_per_participant="n_nodes"` and `max_trials_per_participant="n_nodes"` so each participant completes all three color trials.
- Wrap the trial maker in a `Timeline` with a short `InfoPage` welcome page and a short `InfoPage` thank-you page.
- Configure bots to submit valid ratings through the native `RatingControl` path, preserving browser/bot response parity.
- Include the standard support files needed for PsyNet local launch checks, including `config.txt`, `requirements.txt` or constraints as needed, and `.gitignore`.
- Evidence after approval should include `python experiment.py`, `psynet test local`, a participant-flow recording or targeted screenshots, exported data showing one rating per color, a monitor snapshot, and `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output <absolute evidence path>`.

### Key decisions

| Decision | Choice | Status |
|---|---|---|
| Base demo | `~/PsyNet/demos/experiments/simple_audio_rating/experiment.py`, simplified from audio assets to color prompts. | Recommended default |
| Experiment architecture | `Experiment` + `Timeline` + `InfoPage` + `StaticTrialMaker` + `StaticTrial` + native `ModularPage`. | Recommended default |
| Data schema highlights | `color_name`, `hsl`, and trial answer `rating`; validation confirms one row per color. | Recommended default |
| Testing and evidence plan | Run local PsyNet functional, participant-flow, export, monitor, and performance checks before completing the attempt. | Required after approval |

## Decision log

- 2026-06-12 — Purpose: chose simple implementation / technical demo over replication or new science because the public challenge asks only for a simple runnable PsyNet experiment with fixed color-rating trials; inferred from challenge instructions.
- 2026-06-12 — Science scope: chose no hypothesis-driven science section over inventing a research question because the challenge does not ask for scientific inference; inferred from challenge instructions.
- 2026-06-12 — Design: chose a within-participant fixed three-trial design over between-participant color assignment because the challenge says the participant is shown each primary color in turn; inferred from challenge instructions.
- 2026-06-12 — Trial architecture: chose static trials over chain/network architecture because each color rating is independent and no participant response creates later stimulus state; inferred from challenge instructions and the simple-round-structure checklist.
- 2026-06-12 — Stimulus rendering: chose native `ColorPrompt` over custom HTML/CSS because current PsyNet provides a first-class color prompt and the challenge does not require bespoke UI; default, overridable.
- 2026-06-12 — Response control: chose native `RatingControl(values=7)` over a custom slider or multi-rating form because the task needs one 1-7 pleasantness rating per trial; default, overridable.
- 2026-06-12 — Evidence plan: chose local PsyNet functional, participant-flow, export, monitor, and performance evidence over deployment evidence because challenge attempts use local ephemeral PsyNet/Dallinger defaults; default, overridable.
