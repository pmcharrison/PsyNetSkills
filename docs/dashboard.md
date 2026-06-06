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

## Design principles

The dashboard should stay simple and deterministic. It should not require a
database, external API, or JavaScript build pipeline. Python owns repository
parsing; Hugo owns Markdown rendering and static site generation.

Giscus comments can be added once the GitHub repository discussion settings are
finalized.
