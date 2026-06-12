---
name: dashboard-preview-links
description: Share deterministic dashboard PR preview links immediately after creating or updating a pull request.
authors: [pmcharrison]
---

# Dashboard preview links

Use this skill before sharing dashboard preview links after creating or updating
a pull request. Return immediately; do not wait for GitHub Actions or GitHub
Pages.

## Workflow

1. Identify the PR number and branch name:

   ```bash
   branch="$(git branch --show-current)"
   ```

2. Build these links:

   ```text
   https://pmcharrison.github.io/PsyNetSkills/pr-preview/pr-<number>/
   https://github.com/pmcharrison/PsyNetSkills/actions/workflows/dashboard-preview.yml?query=branch%3A<branch-name>
   ```

   URL-encode slashes in the branch name when writing the workflow-runs link
   (for example, `cursor/example` becomes `cursor%2Fexample`).

3. Tell the user that the preview target is the first link and will publish
   there once GitHub Actions and GitHub Pages finish. Also include the
   branch-filtered workflow-runs link so they can check freshness.

4. State the freshness risk plainly:
   - For a new pull request, the preview URL may return 404 until publishing
     finishes.
   - For an existing pull request, the preview URL may show an older build until
     publishing finishes for the latest commit.
   - If the pull request comes from a fork, the preview workflow does not publish
     because it requires write access to `gh-pages`.

5. For challenge attempts, use the direct challenge attempt page as the preview
   target:

   ```text
   https://pmcharrison.github.io/PsyNetSkills/pr-preview/pr-<number>/challenges/<challenge-slug>/<attempt-name>/
   ```

   For plan-review pauses, append the relevant anchor, such as `#plan`.

## Rules

- Do not use the commit `/checks` URL as the source of truth for this repository;
  it can show no checks even when pull-request workflow runs exist.
- Do not poll GitHub Actions or GitHub Pages before responding.
- Always include the deterministic preview target and the branch-filtered
  workflow-runs link.
- Do not imply that the preview reflects the latest commit unless the user has
  provided fresh external evidence that publishing has completed.
