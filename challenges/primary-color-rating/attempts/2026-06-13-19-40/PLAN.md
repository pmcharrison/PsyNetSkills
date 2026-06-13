# Plan

## Methods

Participants will complete a short subjective rating task. After a welcome page,
they will see three color trials, one each for red, green, and blue. Each trial
will show a large color swatch and ask: "How pleasant is this color?" The
participant will answer on a 1 to 7 scale, where 1 means "Not at all pleasant"
and 7 means "Very pleasant." The experiment will save one numeric rating for
each color.

The trial order will be randomized across participants using PsyNet's static
trial machinery. The materials are the three primary color stimuli, represented
as structured node definitions containing a color name and CSS color value. The
participant workflow will be:

1. Welcome page explaining the task.
2. Three color-rating trials.
3. Thank-you page.

No external services, credentials, audio, or uploaded assets are needed.

## Implementation

The experiment will live in `code/primary_color_rating/` so the package name
does not collide with Python's standard-library `code` module. I will start from
PsyNet's minimal `hello_world` and `simple_audio_rating` patterns, then keep the
implementation small:

- Define three `StaticNode` objects with `color_name` and `hex_color`.
- Implement a `ColorRatingTrial(StaticTrial)` whose `show_trial` returns a
  `ModularPage`.
- Use a custom prompt or compact HTML prompt to display a centered color swatch
  and the color name.
- Use `RatingControl(values=7, min_description="Not at all pleasant",
  max_description="Very pleasant")` so the formatted answer is a single rating.
- Use `StaticTrialMaker` with `expected_trials_per_participant="n_nodes"` and
  `max_trials_per_participant="n_nodes"` so each participant rates each color
  exactly once.
- Add `InfoPage` instances for the welcome and thank-you pages.
- Set bot behavior to provide valid ratings for simulation and local automated
  testing.
- Include standard PsyNet support files, including `.gitignore`,
  `requirements.txt`, and generated constraints if required by the local PsyNet
  workflow.

The primary saved datum for each trial will be the participant response, with
the corresponding static node definition identifying the rated color. If the
default export makes color/rating joins awkward, I will add a small analysis
helper in the notebook rather than changing the experiment's participant-facing
behavior.

## Validation and evidence

After human approval of this plan, I will implement the experiment and collect
the required challenge evidence:

- Run `python experiment.py` from `code/primary_color_rating/` to catch import
  and configuration errors.
- Run `psynet test local` to exercise the PsyNet local participant flow.
- Run `psynet simulate` with enough bots to produce multiple ratings per color,
  and save the export as `evidence/simulated_data.zip`.
- Write `evidence/analyses/analysis.ipynb` to read the simulated export, show
  one row per saved rating, summarize ratings by color, plot the color means,
  and verify that each simulated participant produced one rating for red, green,
  and blue.
- Run `psynet performance-test local --n-bots 40 --duration-minutes 5
  --time-factor 1.0 --json-output <attempt>/evidence/performance.json` unless
  the local environment blocks it; if blocked, record the command output and
  blocker in `EVALUATION.md`.
- Use the participant evidence workflow to save targeted screenshots and a short
  `evidence/participant.mp4` showing the welcome page, representative color
  trials, rating submission, and thank-you page.
- Save a PsyNet monitor snapshot as `evidence/monitor.html`.
- Write `REPORT.md` summarizing implementation, validation, simulation,
  analysis, and any unresolved blockers.

The attempt will remain marked in progress until the implementation, evidence,
analysis notebook, report, and final metadata are complete.
