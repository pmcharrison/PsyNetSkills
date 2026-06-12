---
name: dashboard-preview-polling
description: Poll the dashboard PR preview workflow before sharing preview links. Use when a Cursor Cloud Agent creates or updates a PR and needs to tell the user whether the dashboard preview reflects the latest pushed commit.
authors: [pmcharrison]
---

# Dashboard preview polling

Use this skill before sharing dashboard preview links after creating or updating
a pull request.

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

3. Poll for up to 75 seconds for a `Deploy dashboard PR preview` workflow run
   whose `headSha` equals the latest pushed commit SHA:

   ```bash
   deadline=$((SECONDS + 75))
   while [ "$SECONDS" -lt "$deadline" ]; do
     gh run list \
       --workflow "Deploy dashboard PR preview" \
       --branch "$branch" \
       --limit 10 \
       --json headSha,status,conclusion,url,createdAt
     sleep 5
   done
   ```

4. If the matching run completes successfully, read the latest `gh-pages` commit
   SHA and poll the GitHub Pages deployment workflow for that SHA:

   ```bash
   pages_sha="$(git ls-remote origin gh-pages | awk '{print $1}')"
   deadline=$((SECONDS + 75))
   while [ "$SECONDS" -lt "$deadline" ]; do
     gh run list \
       --workflow "pages-build-deployment" \
       --branch "gh-pages" \
       --limit 10 \
       --json headSha,status,conclusion,url,createdAt
     sleep 5
   done
   ```

   The Pages deployment can still be in progress after the preview workflow has
   pushed files to `gh-pages`; during that window the preview URL may return 404.

5. If both the matching preview run and the matching Pages deployment complete
   successfully within the polling windows, tell the user the dashboard preview
   has been rebuilt and published for the latest commit and print the preview URL
   only. Do not print workflow run links in the user-facing response unless the
   user asks for them.

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
   deployment has published the latest `gh-pages` state, then print the preview
   URL only.

7. If no matching preview run appears within 75 seconds, do not say the preview build was
   triggered. Tell the user no preview run has appeared yet for the latest
   commit, and print the workflow-runs link.

8. If a matching preview run appears but does not complete successfully within 75
   seconds, do not imply the preview is current. Tell the user the preview build
   is still pending or not successful for the latest commit, and print the
   workflow-runs link instead of relying on the preview URL.

9. If the matching preview run succeeds but the matching Pages deployment is
   missing, pending, unsuccessful, or cancelled without a newer successful Pages
   deployment, tell the user the preview files were built but may not be
   published yet. Print the Pages workflow-runs link instead of relying on the
   preview URL.

## Rules

- Do not use the commit `/checks` URL as the source of truth for this repository;
  it can show no checks even when pull-request workflow runs exist.
- Always compare the workflow run `headSha` with `git rev-parse HEAD`.
- After the preview workflow succeeds, also compare the `pages-build-deployment`
  run `headSha` with the latest `gh-pages` SHA from `git ls-remote origin
  gh-pages`.
- If the matching run is completed with a non-success conclusion, print the
  workflow run URL and conclusion.
- If no matching run appears, say that no preview run has appeared for the latest
  commit yet.
- If the workflow run is still queued or in progress after 75 seconds, print the
  branch-filtered workflow-runs link.
- If the matching preview run succeeds but Pages deployment is still queued or in
  progress, print the Pages workflow-runs link.
- If the matching Pages deployment was cancelled but a newer Pages deployment
  succeeded, treat the cancelled run as superseded and print only the dashboard
  preview URL.
- If both matching runs succeed, print only the dashboard preview URL.
