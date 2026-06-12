---
name: dashboard-preview-links
description: Share deterministic dashboard PR preview links after briefly polling for publication status.
authors: [pmcharrison]
---

# Dashboard preview links

Use this skill before sharing dashboard preview links after creating or updating
a pull request. Poll briefly for publication status, but always give the user
the deterministic preview URL even if polling times out.

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

3. Poll for up to 75 seconds total for:
   - a `Deploy dashboard PR preview` workflow run for the branch whose `headSha`
     matches the latest pushed commit, and
   - if that preview run succeeds, a successful `pages-build-deployment` run on
     `gh-pages` after the preview run updates `gh-pages`.

   Do not poll the separate `Validate` workflow; preview deployment runs
   independently.

4. If both the preview workflow and Pages deployment complete successfully within
   the polling window, tell the user the preview has been published and provide
   the preview URL.

5. If polling times out, or if a relevant run is queued, in progress, missing,
   cancelled, or failed, provide both the preview target and the branch-filtered
   workflow-runs link. State the freshness risk plainly:
   - For a new pull request, the preview URL may return 404 until publishing
     finishes.
   - For an existing pull request, the preview URL may show an older build until
     publishing finishes for the latest commit.
   - If the pull request comes from a fork, the preview workflow does not publish
     because it requires write access to `gh-pages`.

6. For challenge attempts, use the direct challenge attempt page as the preview
   target:

   ```text
   https://pmcharrison.github.io/PsyNetSkills/pr-preview/pr-<number>/challenges/<challenge-slug>/<attempt-name>/
   ```

   For plan-review pauses, append the relevant anchor, such as `#plan`.

## Rules

- Do not use the commit `/checks` URL as the source of truth for this repository;
  it can show no checks even when pull-request workflow runs exist.
- Do not wait for, or gate on, the separate `Validate` workflow.
- Keep polling bounded to 75 seconds total.
- Always include the deterministic preview target when polling does not confirm
  publication.
- Do not imply that the preview reflects the latest commit unless polling or the
  user has provided fresh evidence that publishing has completed.
