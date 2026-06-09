---
name: make-psynet-merge-request
description: Create or verify merge requests against the upstream PsyNet GitLab repository from this workspace. Use when asked to send PsyNet changes upstream, check whether the agent has PsyNet MR privileges, or poll PsyNet CI for an MR.
authors: [pmcharrison]
---

# Make a PsyNet merge request

Use this skill when the user asks you to create, test, or verify a merge request
against `https://gitlab.com/PsyNetDev/PsyNet`.

## Prerequisites

- Work in the local PsyNet checkout at `~/PsyNet`.
- Use `GITLAB_TOKEN` for non-interactive GitLab authentication. A plain HTTPS
  push may fail with `could not read Username for 'https://gitlab.com'`.
- Confirm the checkout is clean before making changes:
  `git status --short --branch`.
- Follow agent guidelines in `~/PsyNet/AGENTS.md`, including instructions
  on changelog contribution fragments.
- Run PsyNet's `code-review` skill to evaluate the proposed changes
  and discuss any decision points with the user as necessary.

## Check privileges

Verify that the token can see the upstream project and note the returned access
level:

```bash
python - <<'PY'
import json, os, urllib.parse, urllib.request

project = urllib.parse.quote("PsyNetDev/PsyNet", safe="")
request = urllib.request.Request(
    f"https://gitlab.com/api/v4/projects/{project}",
    headers={"PRIVATE-TOKEN": os.environ["GITLAB_TOKEN"]},
)
with urllib.request.urlopen(request, timeout=30) as response:
    data = json.load(response)
print(data["path_with_namespace"])
print(data.get("permissions"))
PY
```

GitLab project access level `30` is Developer access and is sufficient for
pushing branches and opening merge requests in the PsyNet project.

## Create a merge request

1. Fetch the target branch:
   `git fetch origin master`.
2. Create a descriptive branch from `origin/master`.
3. Make the requested changes, test them, commit them, and push with GitLab merge
   request push options.

Use a token-backed push so the command works in non-interactive agent sessions:

```bash
AUTH=$(printf 'oauth2:%s' "$GITLAB_TOKEN" | base64 -w0)
git -c http.extraHeader="Authorization: Basic $AUTH" push -u origin HEAD \
  -o merge_request.create \
  -o merge_request.target=master \
  -o merge_request.title="Your MR title" \
  -o merge_request.description="Concise description of the change."
```

Add `-o merge_request.draft` when the MR is only a test or still needs review
before it is ready.

## Poll CI

After creating the MR, tell the user before starting any CI poll that PsyNet CI
typically takes at least 15 minutes. Then poll GitLab until the latest branch
pipeline reaches a terminal status. This is useful because a merge request is
only actionable once CI has reported success or a concrete failure.

```bash
python - <<'PY'
import itertools, json, os, time, urllib.parse, urllib.request

project = urllib.parse.quote("PsyNetDev/PsyNet", safe="")
branch = os.environ["PSYNET_BRANCH"]
headers = {"PRIVATE-TOKEN": os.environ["GITLAB_TOKEN"]}
interval = int(os.environ.get("PSYNET_POLL_INTERVAL_SECONDS", "30"))
max_polls = os.environ.get("PSYNET_MAX_POLLS")
terminal_statuses = {"success", "failed", "canceled", "skipped", "manual"}
url = (
    f"https://gitlab.com/api/v4/projects/{project}/pipelines"
    f"?ref={urllib.parse.quote(branch, safe='')}&per_page=1"
)

for attempt in itertools.count(1):
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        pipelines = json.load(response)
    if not pipelines:
        print(f"poll {attempt}: no pipeline found yet", flush=True)
    else:
        pipeline = pipelines[0]
        print(
            f"poll {attempt}: {pipeline['id']} {pipeline['status']} "
            f"{pipeline['web_url']}",
            flush=True,
        )
        if pipeline["status"] in terminal_statuses:
            break
    if max_polls is not None and attempt >= int(max_polls):
        raise SystemExit(
            f"Pipeline did not reach a terminal status after {attempt} poll(s)"
        )
    time.sleep(interval)
PY
```

If CI fails, fetch the failing job logs before reporting back:

```bash
python - <<'PY'
import json, os, urllib.parse, urllib.request

project = urllib.parse.quote("PsyNetDev/PsyNet", safe="")
pipeline_id = os.environ["PSYNET_PIPELINE_ID"]
headers = {"PRIVATE-TOKEN": os.environ["GITLAB_TOKEN"]}
request = urllib.request.Request(
    f"https://gitlab.com/api/v4/projects/{project}/pipelines/{pipeline_id}/jobs",
    headers=headers,
)
with urllib.request.urlopen(request, timeout=30) as response:
    jobs = json.load(response)

failed_jobs = [job for job in jobs if job["status"] == "failed"]
if not failed_jobs:
    print("No failed jobs found")

for job in failed_jobs:
    print(f"===== {job['id']} {job['name']} {job['web_url']} =====")
    trace_request = urllib.request.Request(
        f"https://gitlab.com/api/v4/projects/{project}/jobs/{job['id']}/trace",
        headers=headers,
    )
    with urllib.request.urlopen(trace_request, timeout=30) as trace_response:
        print(trace_response.read().decode("utf-8", errors="replace"))
PY
```

Then inspect logs for failed jobs through the GitLab API before changing code.

## Permission-test MRs

When the user only asks whether MR creation is possible, create a draft MR with
an empty commit on a clearly named test branch, verify the MR through the API,
and leave the MR URL in the final response so a maintainer can close it.
