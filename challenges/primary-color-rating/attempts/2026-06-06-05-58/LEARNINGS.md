# Learnings

## `code/` can collide with Python's standard library

**Summary:** A PsyNet experiment placed directly in an attempt folder named
`code/` did not run with `psynet test local`, because Dallinger imports the
current directory by basename and resolved Python's standard-library `code`
module instead of the attempt package. Nesting the runnable experiment in
`code/primary_color_rating/` avoided the collision while keeping the
implementation self-contained.

**Suggestions**

- PsyNetSkills quick fix: Clarify in the attempt instructions that generated
  PsyNet experiments may need a runnable subdirectory under `code/` when the
  framework's package import rules conflict with the attempt folder name.
  Confidence: high.
- PsyNet long-term fix: Avoid importing an experiment package solely by current
  directory basename, or raise a targeted error when the current directory name
  resolves to a non-package module such as Python's standard-library `code`.
  Confidence: high.

**Decision:** Implemented in PsyNetSkills. Notes: The attempt now uses
`code/primary_color_rating/`, and the attempt README documents why.

## Static trials may run in framework-selected order

**Summary:** `StaticTrialMaker` did not preserve the declared color order during
the bot run. The implementation test now checks that one trial exists for each
target color rather than assuming a fixed presentation order.

**Suggestions**

- PsyNetSkills quick fix: Encourage challenge implementations and tests to
  assert scientifically relevant invariants unless the public instructions
  explicitly require a presentation order. Confidence: medium.
- PsyNet long-term fix: Document the default static-trial ordering behavior more
  prominently in `StaticTrialMaker` docs, including how to force a fixed order
  when an experiment requires one. Confidence: low.

**Decision:** Pending. Notes:

## Dashboard basic data needs JSON-friendly values

**Summary:** `get_basic_data(context="monitor")` needs JSON-serializable values
for the dashboard. The export path can still return a DataFrame, but the monitor
path should return plain records.

**Suggestions**

- PsyNetSkills quick fix: Mention in experiment attempt guidance that dashboard
  data checks should exercise `context="monitor"` if `get_basic_data` returns
  pandas objects for export. Confidence: medium.
- PsyNet long-term fix: Make dashboard basic-data rendering convert pandas
  DataFrames to records automatically, matching the exporter's behavior.
  Confidence: medium.

**Decision:** Pending. Notes:

## Local export can prompt for source download credentials

**Summary:** `psynet export local` can prompt for dashboard credentials when
downloading source code. Passing `--no-source` made the data export
noninteractive and better suited to automated challenge evidence collection.

**Suggestions**

- PsyNetSkills quick fix: Use `psynet export local --no-source` in challenge
  evidence instructions when only `evidence/data.zip` is required. Confidence:
  high.
- PsyNet long-term fix: Add a noninteractive export preset for local evidence
  collection that implies `--no-source` when source artifacts are not requested.
  Confidence: medium.

**Decision:** Pending. Notes:
