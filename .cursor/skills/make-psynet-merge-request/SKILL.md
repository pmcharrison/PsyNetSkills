---
name: make-psynet-merge-request
description: Create or verify merge requests against the upstream PsyNet GitLab repository from this workspace. Use when asked to send PsyNet changes upstream, check whether the agent has PsyNet MR privileges, or poll PsyNet CI for an MR.
---

# Make a PsyNet merge request

Use this skill when the user asks you to create, test, or verify a merge request
against `https://gitlab.com/PsyNetDev/PsyNet`.

## Prerequisites

- Work in the local PsyNet checkout at `~/PsyNet`.
- Confirm the checkout is clean before making changes:
  `git status --short --branch`.
- Activate the PsyNet virtual environment when it exists:
  `source .venv/bin/activate`.
- Use `GITLAB_TOKEN` for non-interactive GitLab authentication. A plain HTTPS
  push may fail with `could not read Username for 'https://gitlab.com'`.

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
import json, os, time, urllib.parse, urllib.request

project = urllib.parse.quote("PsyNetDev/PsyNet", safe="")
branch = os.environ["PSYNET_BRANCH"]
headers = {"PRIVATE-TOKEN": os.environ["GITLAB_TOKEN"]}
url = (
    f"https://gitlab.com/api/v4/projects/{project}/pipelines"
    f"?ref={urllib.parse.quote(branch, safe='')}&per_page=1"
)

while True:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        pipelines = json.load(response)
    if not pipelines:
        print("No pipeline found yet")
    else:
        pipeline = pipelines[0]
        print(pipeline["id"], pipeline["status"], pipeline["web_url"])
        if pipeline["status"] in {"success", "failed", "canceled", "skipped"}:
            break
    time.sleep(30)
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
    for job in json.load(response):
        print(job["id"], job["name"], job["status"], job["web_url"])
PY
```

Then inspect logs for failed jobs through the GitLab API before changing code.

## Permission-test MRs

When the user only asks whether MR creation is possible, create a draft MR with
an empty commit on a clearly named test branch, verify the MR through the API,
and leave the MR URL in the final response so a maintainer can close it.
