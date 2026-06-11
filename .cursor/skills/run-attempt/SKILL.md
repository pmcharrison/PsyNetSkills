---
name: run-attempt
description: Start a runnable PsyNet challenge attempt with psynet debug local, public review links, and an opened dashboard for live review.
authors: [pmcharrison]
disable-model-invocation: true
---

# Run an attempt

Use this skill only when explicitly invoked as `/run-attempt` or when the user
asks to start an existing attempt for live interactive review.

## Goal

Start the PsyNet experiment stored in an existing challenge attempt, create
clickable public review links, open the live experiment dashboard/develop page in
the Cursor Desktop browser or remote desktop, show the dashboard credentials, and
leave the server running so the user can take control.

## Workflow

1. Identify the attempt path. Accept either:
   - `challenges/<challenge-slug>/attempts/<attempt-name>`;
   - `<challenge-slug>/<attempt-name>`;
   - the current working directory if it is inside an attempt.
2. Do not create or modify attempt evidence. This workflow is for ad hoc live
   review, not frozen evaluation artifacts.
3. Run a dry run first:
   `uv run python .cursor/skills/run-attempt/scripts/run_attempt.py <attempt> --dry-run`
4. If the dry run resolves exactly one experiment directory, start the live
   server in a tmux session so the user can continue using the agent:
   `tmux -f /exec-daemon/tmux.portal.conf new-session -d -s run-attempt -- uv run python .cursor/skills/run-attempt/scripts/run_attempt.py <attempt>`
5. By default, the helper starts a public localtunnel process for port `5000`.
   Watch the output for the `Run attempt handoff` block. It must include:
   - the local link to start a new participant;
   - the public tunnel link to add/start a new participant;
   - the public tunnel link to the dashboard/develop page;
   - the dashboard username and password.
6. Open the public dashboard/develop URL from the handoff block in the Cursor
   Desktop browser or remote desktop. If a login form appears instead of using
   the embedded URL credentials, log in automatically with the printed username
   and password. Do not ask the user to perform this login manually unless
   automatic login fails.
7. After login, leave the browser on the dashboard/develop page. Tell the user
   which tmux session is running the server and provide all three handoff links
   plus the credentials.

## Helper usage

Run from the repository root:

`uv run python .cursor/skills/run-attempt/scripts/run_attempt.py <attempt>`

Useful options:

- `--dry-run` resolves the experiment and prints the command without starting
  services or the server.
- `--experiment-dir <path>` selects an experiment when an attempt contains more
  than one `experiment.py`.
- `--no-start-services` skips the best-effort PostgreSQL/Redis startup step.
- `--psynet-command <path-or-command>` overrides the detected PsyNet executable.
- `--no-public-tunnel` skips the default localtunnel process and only prints
  local PsyNet URLs.
- `--public-tunnel-port <port>` changes the local port exposed by the default
  public tunnel; PsyNet normally uses `5000`.

## Common failures

- Attempts without `code/**/experiment.py` are not runnable through this skill.
- If multiple experiment directories exist, ask the user which one to run.
- Missing or stale PsyNet dependencies should be fixed in the Cloud Agent
  environment, not by editing the attempt code during this workflow.
- If PsyNet starts but generated commands cannot find runtime tools such as
  `flask`, relaunch with the PsyNet virtualenv on `PATH` or pass
  `--psynet-command /home/ubuntu/PsyNet/.venv/bin/psynet`.
- If no public tunnel URL appears, verify `npx` or `localtunnel` is available
  and relaunch the helper. Plain `127.0.0.1` links only work inside the Cloud VM
  or through Cursor's forwarded-port UI.
- Use only local, ephemeral dashboard credentials. Do not add real service
  credentials just to make a review run succeed.
