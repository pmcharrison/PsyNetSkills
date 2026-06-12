---
name: launch-experiment-for-researcher
description: Launch a local PsyNet experiment for a researcher, share the generated admin dashboard credentials, and open the dashboard in the cloud desktop browser. Use when asked to make a local experiment available for researcher inspection rather than to run participant evidence.
authors: [zeroada]
---

# Launch experiment for researcher

Use this skill when a researcher asks you to start a PsyNet experiment locally
and give them access to the generated Dallinger dashboard.

## Goal

Start the experiment server with `psynet debug local --legacy --no-browsers`,
extract the generated dashboard URL and admin credentials, share them with the
researcher, and verify that the dashboard login works in the cloud desktop
browser.

## Workflow

1. Confirm the experiment directory and use the local PsyNet environment
   expected for the task. If the task is part of PsyNetSkills challenge work,
   refresh and verify the local `~/PsyNet` checkout as required by `AGENTS.md`.
2. Start required services if they are not already running:
   - PostgreSQL, preferring `sudo pg_ctlcluster 16 main start` on Cursor Cloud.
   - Redis, preferring `redis-server --daemonize yes` on Cursor Cloud.
3. Start or reuse a descriptive tmux session for the launch. Prefer a name that
   includes the experiment or task, for example `psynet-debug-local`.
4. In that tmux session, run:
   `psynet debug local --legacy --no-browsers`
5. Watch the tmux output until PsyNet prints the generated dashboard URL,
   administrator username, and administrator password. If the process fails
   before those values appear, fix the concrete environment or experiment error
   and restart the command.
6. Copy the dashboard URL, admin username, and admin password exactly from the
   logs. Treat these as local ephemeral credentials; do not commit them, write
   them into repository files, or include them in public artifacts.
7. Share the URL and credentials with the researcher in the current chat. Make
   clear that they are for the current local debug session only.
8. Use browser automation on the cloud desktop to open the dashboard URL and log
   in with the generated admin credentials.
9. Confirm that the dashboard loads after login. If login fails, re-read the
   latest tmux logs before assuming the credentials are wrong.
10. Leave the tmux session and services running unless the researcher asks you
   to stop them.

## Browser verification

Use the `computerUse` subagent for the cloud desktop login check. Ask it to:

1. Open the generated dashboard URL in Chrome.
2. Enter the generated admin username and password.
3. Submit the login form.
4. Report whether the Dallinger dashboard is visible after login.

Do not use browser automation to expose credentials in screenshots, recordings,
or committed evidence unless the researcher explicitly requests such an artifact
and confirms that local debug credentials may be shown.

## Common failures

- `psynet debug local` may start but never print credentials if PostgreSQL or
  Redis is unavailable. Check the service startup logs and retry after starting
  the missing service.
- Cursor Cloud may deny `service postgresql start`; use `pg_ctlcluster` instead.
- Existing tmux sessions may contain stale credentials from a previous launch.
  Always read the latest output from the active command.
- `--no-browsers` prevents PsyNet from opening browser windows automatically, so
  the agent must open the generated dashboard URL manually.

## Rules

- Use only local, ephemeral PsyNet/Dallinger debug credentials.
- Never configure production service credentials for this workflow.
- Never commit generated dashboard credentials or local runtime logs containing
  credentials.
- If the user asks for participant-flow evidence, use `record-participant-video`
  instead of this skill.
