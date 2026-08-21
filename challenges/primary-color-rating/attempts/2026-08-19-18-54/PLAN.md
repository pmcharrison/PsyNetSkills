# Plan

Dogfooding note: this is an infrastructure test of the challenge-attempt / audit
workflow. Human planning review is skipped as allowed for dogfooding.

## Methods

Participants complete a short, single-session pleasantness rating task. After a
welcome page, each participant sees three primary colors — red, green, and blue —
as separate trials. On each trial a colored patch is shown and the participant
rates how pleasant the color is on a 1–7 scale. One rating is stored per color.
A thank-you page ends the session. There are no between-participant conditions
and no randomization requirements beyond PsyNet's default trial-maker balancing.

## Implementation

- Scaffold a nested experiment at `code/primary_color_rating/` with
  `psynet setup --psynet-source editable` against the local `~/PsyNet` checkout.
- Use `InfoPage` for welcome and thank-you text.
- Use `StaticNode` / `StaticTrial` / `StaticTrialMaker` with three nodes
  (`red`, `green`, `blue`), presenting each color via `ColorPrompt` (HSL) and
  collecting a single 1–7 rating with `RatingControl`.
- Keep `test_n_bots` modest but large enough for a simulation export.
- Validate with `python experiment.py` and `psynet test local`.
- Collect audit artifacts incrementally at the attempt root (not a nested
  `audit/` directory): test logs, simulated data zip, analysis notebook,
  performance smoke output when feasible, and honest blockers for anything
  that cannot be produced in this dogfood run.
