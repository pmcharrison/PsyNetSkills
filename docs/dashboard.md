# Dashboard

The dashboard is a Hugo static site generated from repository files. It renders:

- The public workflow overview from `README.md`.
- Skill summaries from `.cursor/skills/*/SKILL.md`.
- Challenge summaries from `challenges/*`.
- Attempt histories and latest scores when evaluations exist.
- Open learning-action counts from attempt `LEARNINGS.md` files.
- An Actions tab that groups open learning actions through a committed
  `actions-review.yaml` review artifact.

Build it locally with:

```bash
uv run psynetsk-export-dashboard-data
hugo --source dashboard --destination ../public --cleanDestinationDir
```

The Python command exports structured repository data to
`dashboard/data/psynetsk.json`, writes `README.md` to the Hugo index page, and
creates lightweight Hugo content stubs for skills and challenges. Hugo then
renders the workflow overview, generated content, layouts, and final HTML into
`public/`. The GitHub Pages workflow builds the same output in CI.

`actions-review.yaml` is optional. When present, it records an offline
LLM-generated review of currently open learning actions, grouped into thematic
sections that reference stable action IDs. Dashboard builds never call an LLM;
they only parse repository files and render the committed review.

Attempt pages are reviewer-facing artifacts. They may show evaluation criteria
so reviewers can compare the implementation against the rubric, but agents must
not inspect `CRITERIA.md`, prior attempts, or dashboard attempt pages for the
same challenge before implementation and evidence collection are complete.

## Pull request previews

The production dashboard is published from the `gh-pages` branch root. Pull
requests from branches in this repository are built into subdirectories of the
same branch, under `pr-preview/pr-NUMBER/`.
Attempt artifacts are published to a shared content-addressed store under
`artifacts/blobs/sha256/`, so production and preview pages can reuse identical
evidence files instead of copying them into every preview directory.
Large ZIP files from attempt `challenge/` snapshots, generated attempt `code/`
directories, and evidence ZIPs other than `evidence/data.zip` are shown as
metadata-only file entries rather than copied to GitHub Pages.
Attempt screenshots under `evidence/screenshots/` are published with the other
non-ZIP evidence artifacts and rendered as a static carousel on the attempt
page. Use ordered, descriptive filenames and optionally add
`evidence/screenshots/manifest.json` captions so reviewers can scan the flow
without opening every artifact manually.
Deploys publish `gh-pages` as a one-commit snapshot branch. This keeps the live
site and open previews addressable without letting generated dashboard history
grow indefinitely.

The resulting preview URL is
https://OWNER.github.io/REPOSITORY/pr-preview/pr-NUMBER/.

The preview workflow updates one pull request comment with the current preview
URL whenever the PR branch changes. When the PR is merged, the workflow replaces
the preview with static redirects to the production dashboard. When the PR is
closed without merging, the workflow removes the preview directory from
`gh-pages`.

## Design principles

The dashboard should stay simple and deterministic. It should not require a
database, external API, or JavaScript build pipeline. Python owns repository
parsing; Hugo owns Markdown rendering and static site generation.

Giscus comments can be added once the GitHub repository discussion settings are
finalized.
