---
name: dashboard-preview-links
description: Construct a link to the GitHub Pages preview for the current pull request.
authors: [pmcharrison]
---

# Dashboard preview links

This skill constructs a link to the GitHub Pages preview for the current pull request.

## Workflow

1. Identify the PR number, branch name, and latest pushed commit SHA:

   ```bash
   branch="$(git branch --show-current)"
   sha="$(git rev-parse HEAD)"
   ```

2. Construct the PR preview link:

   ```text
   https://pmcharrison.github.io/PsyNetSkills/pr-preview/pr-<number>/
   https://github.com/pmcharrison/PsyNetSkills/actions/workflows/dashboard-preview.yml?query=branch%3A<branch-name>
   ```

   URL-encode slashes in the branch name when writing the workflow-runs link
   (for example, `cursor/example` becomes `cursor%2Fexample`).

3. Where relevant, construct a link to a more specific page.
   For challenge attempts, use the direct challenge attempt page as the preview target:

   ```text
   https://pmcharrison.github.io/PsyNetSkills/pr-preview/pr-<number>/challenges/<challenge-slug>/<attempt-name>/
   ```

   For plan-review pauses, append the relevant anchor, such as `#plan`.
