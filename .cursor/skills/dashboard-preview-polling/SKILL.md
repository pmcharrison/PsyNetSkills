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

4. If the matching run completes successfully within 75 seconds, tell the user
   the dashboard preview has been rebuilt for the latest commit and print the
   preview URL only. Do not print the workflow run link in the user-facing
   response unless the user asks for it.

5. If no matching run appears within 75 seconds, do not say the preview build was
   triggered. Tell the user no preview run has appeared yet for the latest
   commit, and print the workflow-runs link.

6. If a matching run appears but does not complete successfully within 75
   seconds, do not imply the preview is current. Tell the user the preview build
   is still pending or not successful for the latest commit, and print the
   workflow-runs link instead of relying on the preview URL.

## Rules

- Do not use the commit `/checks` URL as the source of truth for this repository;
  it can show no checks even when pull-request workflow runs exist.
- Always compare the workflow run `headSha` with `git rev-parse HEAD`.
- If the matching run is completed with a non-success conclusion, print the
  workflow run URL and conclusion.
- If no matching run appears, say that no preview run has appeared for the latest
  commit yet.
- If the workflow run is still queued or in progress after 75 seconds, print the
  branch-filtered workflow-runs link.
- If the matching run succeeds, print only the dashboard preview URL.
