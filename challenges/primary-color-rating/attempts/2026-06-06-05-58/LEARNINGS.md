# Learnings

## Implementation notes

- A PsyNet experiment placed directly in an attempt folder named `code/` does not
  run with `psynet test local`, because Dallinger imports the current directory by
  basename and can collide with Python's standard-library `code` module. Nesting
  the runnable experiment in `code/primary_color_rating/` avoided the collision
  while keeping the implementation self-contained inside `code/`.
- `StaticTrialMaker` did not preserve the declared color order during the bot run.
  The implementation test now checks that one trial exists for each target color,
  rather than assuming a fixed presentation order.
- `get_basic_data(context="monitor")` needs JSON-serializable values for the
  dashboard. The export path can still return a DataFrame, but the monitor path
  should return plain records.
- `psynet export local` may prompt for dashboard credentials when downloading
  source code. Passing `--no-source` made the data export noninteractive and
  better suited to automated challenge evidence collection.

## Suggested PsyNetSkills improvements

- Add `LEARNINGS.md` to the standard attempt template so implementation feedback
  is captured while it is fresh.
- Render `LEARNINGS.md` on attempt dashboard pages, near the evaluation and
  evidence summaries, so maintainers can quickly find repo, PsyNet, and challenge
  improvement ideas.
- Clarify in the attempt instructions that generated PsyNet experiments may need
  a runnable subdirectory under `code/` if a framework import rule conflicts with
  the attempt folder name.

## Suggested PsyNet improvements

- Avoid importing an experiment package solely by the current directory basename,
  or document the `code/` folder collision explicitly in local testing errors.
- Add a noninteractive export preset for local evidence collection that implies
  `--no-source` when only data artifacts are needed.
- Consider making dashboard basic-data rendering handle pandas DataFrames by
  converting them to records automatically, matching the exporter's behavior.

## Suggested challenge improvements

- State whether trial order matters. For this challenge, any order seems
  scientifically acceptable as long as red, green, and blue each receive exactly
  one rating.
- Mention that the default PsyNet consent page is acceptable for the challenge,
  or specify a required consent text if evaluators expect one.
