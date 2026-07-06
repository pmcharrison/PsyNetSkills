# Experiment review bundles

An experiment review bundle is a portable folder, conventionally named
`review/`, that contains the materials needed to inspect a standalone PsyNet
experiment implementation. It generalizes the challenge-attempt review workflow
without requiring the PsyNetSkills dashboard or challenge structure.

The review bundle should help a reviewer answer three questions:

1. What experiment was implemented?
2. What was run to validate it?
3. Which artifacts prove the participant flow, data export, analysis, and
   technical checks are ready for review?

The command-line interface for this workflow is `psynet-review-bundle`.
`psynet-review` remains as a compatibility alias. The long-term target is a
small formal tool with flexible agent instructions around it: the CLI should
enforce structure, safety, validation, and rendering, while agents choose the
meaningful screenshots, write the report, and record blockers honestly.

## Folder layout

Use this layout for a complete review bundle:

```text
review/
review.json
PROMPT.md
PLAN.md
TIMELINE.md
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

`review.json` is the review bundle manifest. It indexes artifacts, provenance,
checks, and blockers. The source files remain the durable artifacts; the
manifest explains how they should be interpreted.

`PROMPT.md`, `PLAN.md`, `TIMELINE.md`, and `REPORT.md` are default Markdown
context sections. Agents can remove a file and its section entry from
`review.json` when it is not relevant.

`artifacts/` contains participant-facing media and technical outputs.
`analyses/` contains the executed analysis notebook or equivalent analysis
outputs. `logs/` contains concise command logs, especially for failed or blocked
checks. `site/` is generated output and should normally be ignored by Git.

## Manifest contract

The draft JSON Schema lives at `schemas/review.schema.json`. A minimal example
lives at `examples/review/review.json`.

The manifest records:

- `schema_version`: version of the review bundle manifest schema.
- `created_at` and `updated_at`: ISO 8601 timestamps.
- `experiment`: source path, optional slug, git commit, PsyNet version, and
  optional entry point. The rendered display title is inferred from the review
  folder location unless `experiment.title` is explicitly provided.
- `implementation`: short implementation description and optional notes.
- `environment`: operating system, Python version, PsyNet checkout, and local
  services used.
- `sections`: ordered, optional display sections such as prompt, plan, timeline,
  report, evidence, files, checks, and blockers.
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

Section records use:

- `id`: stable lowercase snake-case section ID.
- `title`: displayed heading.
- `kind`: `markdown`, `evidence`, `files`, `checks`, or `blockers`.
- `path`: required for `markdown` sections.
- `display`: optional boolean. Set to `false` to keep a section in the manifest
  without showing it by default.

## CLI surface

The first implemented commands are:

- `psynet-review-bundle init`, which creates a starter `review/` folder,
  `review.json`, default Markdown section files, artifact directories, analysis
  directory, and logs directory.
- `psynet-review-bundle validate`, which checks `review/review.json`, required
  artifact paths, blocker coverage, report presence, video limits, and notebook
  JSON readiness.
- `psynet-review-bundle render`, which reads `review/review.json`, publishes
  present artifacts through the shared sanitizer and content-addressed artifact
  store, and writes a static review bundle page.

The intended CLI surface is:

- `psynet-review-bundle init`: create `review/`, `review.json`, default section
  files, and ignored output directories.
- `psynet-review-bundle validate`: validate `review.json`, required paths, video
  limits, notebook JSON, and blocker coverage.
- `psynet-review-bundle render`: build `review/site/` as a self-contained static
  review bundle page.
- `psynet-review-bundle archive`: produce a shareable review bundle archive.

A minimal workflow is:

```bash
psynet-review-bundle init
psynet-review-bundle validate
psynet-review-bundle render
```

`psynet-review-bundle init` does not run PsyNet or collect artifacts. It creates a
valid starter manifest whose incomplete required artifacts are covered by
starter blockers. Replace those blockers as artifacts are collected.
The commands default to the conventional `review/` directory; pass a path only
when using a nonstandard review bundle directory.

Artifact collection is intentionally not part of the core CLI contract. Agents
should be free to run the experiment, debug failures, adjust commands, choose
meaningful screenshots, and document blockers using whatever workflow is
appropriate for the experiment. The review bundle contract is the resulting
folder: sections, artifacts, `review.json`, blockers, validation, and rendering.

## Current implementation

The current implementation has three working `psynet-review-bundle` commands:

```bash
psynet-review-bundle init
psynet-review-bundle validate
psynet-review-bundle render
```

`init` creates a starter review bundle whose required-but-missing artifacts are
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
- `psynetsk_tools.review_html` owns the shared evidence-section HTML used by
  standalone review bundles and dashboard attempt pages.
- The dashboard exporter writes `evidence_view` and `evidence_html` for each
  attempt, and the dashboard attempt template embeds the exported HTML inside
  the surrounding Hugo page shell.

The artifact-producing workflow is specified in the
`produce-review-bundle` skill. That skill describes how agents should
initialize `review/`, collect evidence, update `review.json`, write section
files, and document blockers without hard-coding artifact collection into the
CLI.

## Planned next steps

The shared renderer now keeps Hugo responsible for the full workshop dashboard,
routing, navigation, and surrounding page layout, while Python owns the
review-specific evidence UI used by both standalone review bundles and challenge
attempts.

Useful follow-up work includes:

- Improve standalone report rendering beyond escaped preformatted Markdown.
- Add notebook preview parity for markdown, code, text/plain, HTML, and SVG
  outputs where safe.
- Decide whether `psynet-review-bundle` should remain in `psynetsk_tools`, move
  into PsyNet itself, or become a small standalone package once the workflow
  stabilizes.

The `produce-review-bundle` skill owns the judgment-heavy workflow around the
CLI contract. It tells agents when to initialize `review/`, how to choose
meaningful screenshots, when video evidence is worth recording, how to keep
participant-flow scripts with the experiment source, how to write section files,
and how to describe missing evidence without implying that skipped checks
passed. The skill uses the CLI as the formal contract (`init`, `validate`, and
`render`), but leaves experiment-specific decisions such as what participant
states to document, what analysis is scientifically relevant, and which blockers
are acceptable to the agent/human review loop.

Customization should also live primarily in the specification and manifest
rather than in bespoke code. Users should be able to add extra artifacts, mark
standard artifacts as not applicable, add experiment-specific checklist items,
and provide display labels or notes in `review.json`. Renderers should preserve
unknown artifacts as additional files, and future styling customization can start
with a simple optional CSS file (for example `review/style.css`) before
considering custom templates.

## Scope boundary

`psynet-review-bundle validate` should validate structural readiness, not scientific
validity. It can say whether the bundle is complete, safe to render, and
internally consistent. The reviewer and `REPORT.md` remain responsible for
judging whether the experiment design, implementation, and analysis are
scientifically convincing.
