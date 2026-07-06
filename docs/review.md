# Experiment reviews

An experiment review is a portable folder, conventionally named `review/`, that
contains the materials needed to inspect a standalone PsyNet experiment
implementation. It generalizes the challenge-attempt review workflow without
requiring the PsyNetSkills dashboard or challenge structure.

The review folder should help a reviewer answer three questions:

1. What experiment was implemented?
2. What was run to validate it?
3. Which artifacts prove the participant flow, data export, analysis, and
   technical checks are ready for review?

The command-line interface proposed for this workflow is `psynet-review`. The
long-term target is a small formal tool with flexible agent instructions around
it: the CLI should enforce structure, safety, validation, and rendering, while
agents or humans choose the meaningful screenshots, write the report, and record
blockers honestly.

## Folder layout

Use this layout for a complete review:

```text
review/
review.json
REPORT.md
artifacts/
  participant.mp4
  screenshots/
    manifest.json
  performance.json
  monitor.html
  simulated_data.zip
analyses/
  analysis.ipynb
logs/
site/
```

`review.json` is the review manifest. It indexes artifacts, provenance, checks,
and blockers. The source files remain the durable artifacts; the manifest
explains how they should be interpreted.

`REPORT.md` is the human-readable summary of the implementation, simulation,
analysis, validation, and unresolved issues.

`artifacts/` contains participant-facing media and technical outputs.
`analyses/` contains the executed analysis notebook or equivalent analysis
outputs. `logs/` contains concise command logs, especially for failed or blocked
checks. `site/` is generated output and should normally be ignored by Git.

## Manifest contract

The draft JSON Schema lives at `schemas/review.schema.json`. A minimal example
lives at `examples/review/review.json`.

The manifest records:

- `schema_version`: version of the review manifest schema.
- `created_at` and `updated_at`: ISO 8601 timestamps.
- `experiment`: source path, optional slug, git commit, PsyNet version, and
  optional entry point. The rendered display title is inferred from the review
  folder location unless `experiment.title` is explicitly provided.
- `implementation`: short implementation description and optional plan path.
- `environment`: operating system, Python version, PsyNet checkout, and local
  services used.
- `report`: path to `REPORT.md`.
- `artifacts`: typed artifact records.
- `checks`: validation results.
- `blockers`: explicit missing, failed, or incomplete work.
- `render`: optional metadata for generated static output.

Artifact records use a small shared vocabulary:

- `kind`: `video`, `screenshot`, `notebook`, `data_export`, `performance`,
  `monitor_snapshot`, `log`, `report`, `source`, or `other`.
- `status`: `present`, `missing`, `blocked`, or `not_applicable`.
- `created_by`: `agent`, `cli`, `manual`, or `unknown`.

Required artifacts should either have `status: "present"` and an existing path,
or a blocker that explains what was attempted, what failed, and the next step.
Missing artifacts should never be presented as passing checks.

## CLI surface

The first implemented commands are:

- `psynet-review init`, which creates a starter `review/` folder, `review.json`,
  `REPORT.md`, artifact directories, analysis directory, and logs directory.
- `psynet-review validate`, which checks `review/review.json`, required
  artifact paths, blocker coverage, report presence, video limits, and notebook
  JSON readiness.
- `psynet-review render`, which reads `review/review.json`, publishes present
  artifacts through the shared sanitizer and content-addressed artifact store,
  and writes a static review page.

The intended CLI surface is:

- `psynet-review init`: create `review/`, `review.json`, `REPORT.md`, and
  ignored output directories.
- `psynet-review validate`: validate `review.json`, required paths, video
  limits, notebook JSON, and blocker coverage.
- `psynet-review render`: build `review/site/` as a self-contained static
  review report.
- `psynet-review archive`: produce a shareable `review.zip`.

A minimal workflow is:

```bash
psynet-review init
psynet-review validate
psynet-review render
```

`psynet-review init` does not run PsyNet or collect artifacts. It creates a
valid starter manifest whose incomplete required artifacts are covered by
starter blockers. Replace those blockers as artifacts are collected.
The commands default to the conventional `review/` directory; pass a path only
when using a nonstandard review directory.

Artifact collection is intentionally not part of the core CLI contract. Agents
and humans should be free to run the experiment, debug failures, adjust commands,
choose meaningful screenshots, and document blockers using whatever workflow is
appropriate for the experiment. The review contract is the resulting folder:
artifacts, `review.json`, `REPORT.md`, blockers, validation, and rendering.

## Current implementation

The current implementation has three working `psynet-review` commands:

```bash
psynet-review init
psynet-review validate
psynet-review render
```

`init` creates a starter review folder whose required-but-missing artifacts are
covered by starter blockers. `validate` checks the manifest structure, required
artifact files, blocker coverage, video limits, and notebook JSON readiness.
`render` builds a standalone static HTML page from `review.json` and the present
artifacts.

The implementation also shares several pieces with the PsyNetSkills dashboard:

- `psynetsk_tools.review_artifacts` owns credential redaction, static monitor
  snapshot sanitization, shared monitor assets, and content-addressed artifact
  publication.
- `psynetsk_tools.review_model` owns evidence classification for participant
  video, screenshots, screenshot captions, performance JSON, monitor snapshots,
  data exports, analysis notebooks, visible files, and completeness rows.
- The dashboard exporter writes the shared `evidence_view` for each attempt, and
  the dashboard attempt template consumes that exported view instead of
  recomputing evidence classification in Hugo.

## Planned next steps

The next design goal is to make the standalone renderer and dashboard renderer
share more of the same evidence presentation logic without making
`psynet-review` depend on Hugo. The intended direction is:

1. Move evidence-section HTML rendering into a Python module, for example
   `psynetsk_tools.review_html`, which renders a `ReviewEvidenceView`.
2. Use that renderer from `psynet-review render`.
3. Export `evidence_html` from the dashboard data, alongside `evidence_view`.
4. Let the Hugo attempt page embed the exported evidence HTML inside the
   existing attempt page shell.

This would keep Hugo responsible for the full workshop dashboard, routing,
navigation, and surrounding page layout, while Python owns the review-specific
evidence UI used by both standalone reviews and challenge attempts.

After that, useful follow-up work includes:

- Improve standalone report rendering beyond escaped preformatted Markdown.
- Add notebook preview parity for markdown, code, text/plain, HTML, and SVG
  outputs where safe.
- Write a clear review specification that tells an agent which artifacts to
  produce, how to update `review.json`, and how to document blockers.
- Add an agent skill for producing `review/` folders during standalone PsyNet
  experiment implementation.
- Decide whether `psynet-review` should remain in `psynetsk_tools`, move into
  PsyNet itself, or become a small standalone package once the workflow
  stabilizes.

The review specification should describe the artifact-producing workflow without
requiring hard-coded collection subcommands. It can give example commands such
as `psynet simulate`, `psynet performance-test`, notebook execution, monitor
snapshot capture, and Playwright screenshot/video scripts, but those examples
should be guidance rather than mandatory interfaces. The agent should be allowed
to adapt commands, rerun failed steps, choose a different visual-review profile,
or mark an artifact as not applicable when the experiment design justifies it.
The important invariant is that the final `review/` folder records what was
produced, what was attempted, what remains blocked, and how a reviewer can
inspect the result.

The standalone review agent skill should own the judgment-heavy workflow around
that specification. It should tell agents when to initialize `review/`, how to
choose meaningful screenshots, when video evidence is worth recording, how to
keep participant-flow scripts with the experiment source, how to write
`REPORT.md`, and how to describe missing evidence without implying that skipped
checks passed. The skill should use the CLI as the formal contract (`init`,
`validate`, and `render`), but leave experiment-specific decisions such as what
participant states to document, what analysis is scientifically relevant, and
which blockers are acceptable to the agent/human review loop.

Customization should also live primarily in the specification and manifest
rather than in bespoke code. Users should be able to add extra artifacts, mark
standard artifacts as not applicable, add experiment-specific checklist items,
and provide display labels or notes in `review.json`. Renderers should preserve
unknown artifacts as additional files, and future styling customization can start
with a simple optional CSS file (for example `review/style.css`) before
considering custom templates.

## Scope boundary

`psynet-review validate` should validate structural readiness, not scientific
validity. It can say whether the review is complete, safe to render, and
internally consistent. The reviewer and `REPORT.md` remain responsible for
judging whether the experiment design, implementation, and analysis are
scientifically convincing.
