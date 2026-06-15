# Plan

## Methods

Participants will complete a short color-pleasantness rating task. After a brief welcome page, each participant will see three trials in a fixed order: red, green, and blue. On each trial, the current color will be shown as a large swatch and the participant will answer the question "How pleasant is this color?" on a 1 to 7 scale, where 1 means "Not at all pleasant" and 7 means "Extremely pleasant." The experiment will save one numeric rating for each color and then show a short thank-you page.

The design has one within-participant factor, color, with three levels: red, green, and blue. There is no randomization planned because the public instructions ask for the colors to be presented in turn. The only response variable is the pleasantness rating for the displayed color.

## Implementation

The experiment will live under `code/primary_color_rating/` so the runnable PsyNet package does not collide with Python's standard-library `code` module. The implementation will follow PsyNet's static-trial pattern:

- Define three `StaticNode` objects with color metadata such as name, display label, and CSS value.
- Define a `ColorRatingTrial(StaticTrial)` whose `show_trial` returns a `ModularPage`.
- Render the color stimulus with a small HTML prompt using `markupsafe.Markup`, including an accessible label and a large centered swatch.
- Use `RatingControl(values=7, min_description="Not at all pleasant", max_description="Extremely pleasant")` to collect the 1 to 7 response.
- Use `StaticTrialMaker` with `expected_trials_per_participant="n_nodes"` so each participant receives one trial per color.
- Wrap the trial maker between `InfoPage` welcome and thank-you pages in a `Timeline`.
- Add a lightweight bot response strategy so `psynet test local`, simulations, and performance tests can complete without manual input.

The experiment should have no external service dependencies, no custom credentials, and no media assets.

## Validation

After human review approves this plan, validation will focus on the user-visible requirements and local PsyNet health:

- Run `python experiment.py` from the experiment directory to catch import or syntax errors.
- Run `psynet test local` to verify a local participant/bot can complete the experiment and that one trial per color is generated.
- Add a Playwright participant-flow test with assertions that the welcome page, red/green/blue rating trials, and thank-you page appear, and that three ratings can be submitted.
- Capture targeted participant-flow screenshots and, if feasible, a short participant-flow video using the repository recording skill.
- Run `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output <absolute evidence path>` after functional checks pass.
- Export local experiment data to `evidence/data.zip` and include a monitor snapshot when the local debug/test workflow makes it available.

Implementation should pause here until the human user has reviewed and approved this plan.
