---
name: dashboard-preview-links
description: Share durable dashboard PR preview links and workflow status after briefly polling for publication status.
authors: [pmcharrison]
---

# Dashboard preview links

Use this skill after creating or updating a pull request that affects dashboard,
documentation, skill, or challenge-attempt pages. These durable GitHub Pages PR
preview links complement live tunnel previews: live links are immediate but may
expire, while PR preview links support asynchronous review but may take a few
minutes to build.

Poll briefly for publication status, but always give the user the deterministic
preview URL and branch-filtered workflow link if polling does not confirm
publication.

When sharing only the durable preview, use this template:

**Persistent PsyNetSkills preview link:** {pr-preview-url}  
*(This might take a couple of minutes to build. Check build status here:
{workflow-url})*

To publish your changes, merge the pull request.

## Workflow

1. Identify the PR number, branch name, and latest pushed commit SHA:

   ```bash
   branch="$(git branch --show-current)"
   sha="$(git rev-parse HEAD)"
   ```

2. Build these links:

   ```text
   https://pmcharrison.github.io/PsyNetSkills/pr-preview/pr-<number>/
   https://github.com/pmcharrison/PsyNetSkills/actions/workflows/dashboard-preview.yml?query=branch%3A<branch-name>
   ```

   URL-encode slashes in the branch name when writing the workflow-runs link
   (for example, `cursor/example` becomes `cursor%2Fexample`).

3. Poll for up to 75 seconds total for a `Deploy dashboard PR preview` workflow
   run whose `headSha` equals the latest pushed commit SHA:

   ```bash
   deadline=$((SECONDS + 75))
   while [ "$SECONDS" -lt "$deadline" ]; do
     gh run list \
       --workflow "Deploy dashboard PR preview" \
       --branch "$branch" \
       --limit 10 \
       --json headSha,status,conclusion,url,createdAt,updatedAt
     sleep 5
   done
   ```

   Do not poll or wait for the separate `Validate` workflow; preview deployment
   runs independently.

4. If the matching preview run completes successfully before the deadline, read
   the latest `gh-pages` commit SHA and poll `pages-build-deployment` for the
   remaining time:

   ```bash
   pages_sha="$(git ls-remote origin gh-pages | awk '{print $1}')"
   while [ "$SECONDS" -lt "$deadline" ]; do
     gh run list \
       --workflow "pages-build-deployment" \
       --branch "gh-pages" \
       --limit 10 \
       --json headSha,status,conclusion,url,createdAt,updatedAt
     sleep 5
   done
   ```

   The Pages deployment can still be in progress after the preview workflow has
   pushed files to `gh-pages`; during that window the preview URL may return 404
   or show an older Pages deployment.

5. If both the matching preview run and matching Pages deployment complete
   successfully within the polling window, tell the user the preview has been
   published for the latest commit and provide the preview URL. Include the
   branch-filtered workflow link when the user may want to monitor future builds.

6. If the matching Pages deployment is cancelled, check whether a newer
   `pages-build-deployment` run on `gh-pages` completed successfully after the
   cancelled run was created:

   ```bash
   gh run list \
     --workflow "pages-build-deployment" \
     --branch "gh-pages" \
     --limit 10 \
     --json headSha,status,conclusion,url,createdAt,updatedAt
   ```

   If a newer successful Pages deployment exists, treat the cancelled run as
   superseded. Tell the user the preview files were built and a newer Pages
   deployment has published the latest `gh-pages` state, then provide the preview
   URL.

7. If polling times out, or if a relevant run is queued, in progress, missing,
   cancelled, or failed, provide both the preview target and the branch-filtered
   workflow-runs link. State the freshness risk plainly:
   - For a new pull request, the preview URL may return 404 until publishing
     finishes.
   - For an existing pull request, the preview URL may show an older build until
     publishing finishes for the latest commit.
   - If the pull request comes from a fork, the preview workflow does not publish
     because it requires write access to `gh-pages`.

8. For challenge attempts, use the direct challenge attempt page as the preview
   target:

   ```text
   https://pmcharrison.github.io/PsyNetSkills/pr-preview/pr-<number>/challenges/<challenge-slug>/<attempt-name>/
   ```

   For plan-review pauses, append the relevant anchor, such as `#plan`.

## Rules

- Do not use the commit `/checks` URL as the source of truth for this repository;
  it can show no checks even when pull-request workflow runs exist.
- Always compare the preview workflow run `headSha` with `git rev-parse HEAD`.
- After the preview workflow succeeds, compare the `pages-build-deployment`
  run `headSha` with the latest `gh-pages` SHA from `git ls-remote origin
  gh-pages`.
- Do not wait for, or gate on, the separate `Validate` workflow.
- Keep polling bounded to 75 seconds total.
- If the matching preview run completes with a non-success conclusion, print the
  workflow run URL and conclusion alongside the preview target.
- If no matching preview run appears, say that no preview run has appeared for
  the latest commit yet.
- If the matching Pages deployment was cancelled but a newer Pages deployment
  succeeded, treat the cancelled run as superseded.
- Always include the deterministic preview target when polling does not confirm
  publication.
- Do not imply that the preview reflects the latest commit unless polling or the
  user has provided fresh evidence that publishing has completed.
