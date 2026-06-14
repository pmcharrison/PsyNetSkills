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
psynet-review init review
psynet-review validate review
psynet-review render review
```

`psynet-review init` does not run PsyNet or collect artifacts. It creates a
valid starter manifest whose incomplete required artifacts are covered by
starter blockers. Replace those blockers as artifacts are collected.

Collection commands can be added incrementally:

- `psynet-review collect simulate`
- `psynet-review collect performance`
- `psynet-review collect monitor`
- `psynet-review collect analysis`
- `psynet-review collect participant`

The collection commands should allow partial success. If a command cannot
produce an artifact, it should write a blocker rather than silently omitting the
artifact.

## Scope boundary

`psynet-review validate` should validate structural readiness, not scientific
validity. It can say whether the review is complete, safe to render, and
internally consistent. The reviewer and `REPORT.md` remain responsible for
judging whether the experiment design, implementation, and analysis are
scientifically convincing.
