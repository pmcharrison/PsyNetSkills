# Repository architecture

PsyNetSkills is a single-repository workshop system. It is not a production
service and does not have a database or JavaScript build pipeline. The repository
combines source artifacts, generated dashboard inputs, and validation tooling.

## Main directories

```text
.cursor/skills/  Agent Skills-compatible folders, each with a SKILL.md file.
challenges/      Challenge definitions, criteria, references, and attempts.
dashboard/       Hugo site layouts, content mount, static CSS, and generated inputs.
docs/            Detailed repository specifications for contributors and agents.
psynetsk_tools/  Python validation and dashboard export tools.
tests/           Pytest coverage for repository tooling.
public/          Generated Hugo output, ignored by default.
```

## Data flow

The dashboard is built from ordinary repository files:

1. `uv run psynetsk-export-dashboard-data` reads skills, challenges, attempts,
   evaluations, timelines, learnings, and the optional `actions-review.yaml`.
2. The exporter writes structured data to `dashboard/data/psynetsk.json`.
3. The exporter writes generated Hugo content stubs for skills, actions, and
   challenges.
4. The exporter writes `README.md` to `dashboard/content/_index.md`, making the
   README the source for the public dashboard index page.
5. Hugo renders the final static site into `public/`.

Generated dashboard inputs are ignored by Git. Source files such as `README.md`,
`.cursor/skills/*/SKILL.md`, `challenges/*/INSTRUCTIONS.md`, and attempt
artifacts are the maintained state.

The Actions tab is deterministic at build time. The maintained
`actions-review.yaml` file may contain LLM-generated grouping prose, but Hugo and
the exporter only render that committed artifact and never call an external model.

## Review flow

Cursor Cloud Agents work on branches and submit pull requests. Repository
validation, pytest, dashboard export, Hugo build, and the dashboard preview
workflow are the main review checks. Pull-request previews are published under
`pr-preview/pr-NUMBER/` on the GitHub Pages branch.

## Boundaries

PsyNet itself is expected at `~/PsyNet` when implementing experiments. PsyNet
framework changes should be made in that checkout and submitted upstream; this
repository should record only challenge definitions, attempts, evidence, skills,
and documentation needed for the workshop loop.
