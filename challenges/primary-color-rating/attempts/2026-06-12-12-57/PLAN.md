# Experiment plan: Primary color rating experiment

- **Purpose:** Simple implementation / technical demo — success means a locally runnable PsyNet experiment presents red, green, and blue as separate trials and saves one 1-7 pleasantness rating for each color.
- **Status:** Science out of scope; Method and Implementation under review before coding.

## Science

This attempt is a technical implementation challenge rather than a new scientific study. The experiment measures a participant's subjective pleasantness rating for three primary-color stimuli, but the local implementation and bot validation will not support claims about color preference in any population. The valid review question is whether the PsyNet experiment correctly presents the required colors, collects the required responses, and preserves the resulting data.

## Method

Each participant will first see a short welcome page explaining that they will rate three colors for pleasantness. The main task will contain three fixed, participant-visible trials: red, green, and blue. On each trial, the page will show one large color swatch, name the color in the prompt, ask how pleasant the color is, and require a single response on a 1 to 7 rating scale where 1 means not at all pleasant and 7 means very pleasant. No feedback, score, bonus, demographics, prescreen, practice round, synchronous interaction, or AI involvement is planned because the public instructions specify a minimal locally runnable rating task.

The design is within participant: every participant rates all three colors once. Trial order will be fixed as red, green, then blue so the visible flow matches the instruction to show each primary color in turn and so evidence can directly verify one saved rating per named color. Analysis for review will be descriptive: exported trial data should contain exactly one response per color per completed participant, and any later human-data summary would compute per-color counts and mean pleasantness ratings without treating local bots as scientific evidence.

After the color trials, participants will see a short thank-you page. Completion and failure behavior will use PsyNet's standard local experiment flow and generic recruiter defaults; production recruitment, consent customization, payment, and platform-specific redirects are outside the scope of this challenge attempt.

## Implementation

The implementation will live under `code/primary_color_rating/` inside this attempt. It will use the current local PsyNet checkout and follow the static-rating pattern from `~/PsyNet/demos/experiments/simple_audio_rating/experiment.py`, simplified for visual color swatches instead of audio assets, with the minimal `InfoPage` timeline style from `~/PsyNet/demos/experiments/hello_world/experiment.py`.

The core PsyNet structure will be an `Experiment` subclass whose `Timeline` contains a welcome `InfoPage`, a `StaticTrialMaker`, and a thank-you `InfoPage`. The `StaticTrialMaker` will define three `StaticNode` objects with color metadata (`color_name`, `hex_color`, and `display_order`) and a custom `StaticTrial` will render each trial as a `ModularPage` with a color-swatch HTML prompt and `RatingControl(values=7)`. Each trial answer should save the 1-7 pleasantness rating while the node definition identifies which color was rated.

Validation after approval will run `python experiment.py`, `psynet test local`, a scripted participant-flow check with screenshots/video as needed, `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output <attempt>/evidence/performance.json`, and a local export into `evidence/data.zip` if the PsyNet environment permits. Evidence will document any environment blockers explicitly rather than presenting skipped checks as passed.

---

The full binding specification — section status, per-stage decision tables, decision log, and the exact technical plan — is in `PLAN_DETAILS.md` in this folder. Implementation must follow that file exactly.
