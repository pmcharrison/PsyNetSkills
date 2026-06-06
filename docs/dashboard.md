# Dashboard

The dashboard is a Hugo static site generated from repository files. It renders:

- Markdown pages from `docs/`.
- Skill summaries from `.cursor/skills/*/SKILL.md`.
- Challenge summaries from `challenges/*`.
- Attempt histories and latest scores when evaluations exist.

Build it locally with:

```bash
uv run psynetsk-export-dashboard-data
hugo --source dashboard --destination ../public --cleanDestinationDir
```

The Python command exports structured repository data to
`dashboard/data/psynetsk.json` and creates lightweight Hugo content stubs for
skills and challenges. Hugo then renders Markdown, layouts, and final HTML into
`public/`. The GitHub Pages workflow builds the same output in CI.

## Pull request previews

The production dashboard is published from the `gh-pages` branch root. Pull
requests from branches in this repository are built into subdirectories of the
same branch, under `pr-preview/pr-<number>/`.

The resulting preview URL is
https://<owner>.github.io/<repository>/pr-preview/pr-<number>/.

The preview workflow updates one pull request comment with the current preview
URL whenever the PR branch changes. When the PR closes, the workflow removes the
preview directory from `gh-pages`.

## Design principles

The dashboard should stay simple and deterministic. It should not require a
database, external API, or JavaScript build pipeline. Python owns repository
parsing; Hugo owns Markdown rendering and static site generation.

Giscus comments can be added once the GitHub repository discussion settings are
finalized.
