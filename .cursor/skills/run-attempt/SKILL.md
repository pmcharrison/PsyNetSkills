---
name: run-attempt
description: Start a runnable PsyNet challenge attempt with psynet debug local, an opened Cloud Desktop dashboard, credentials, and optional public tunnel links for live review.
authors: [lucasgautheron]
disable-model-invocation: true
---

# Run an attempt

Use this skill only when explicitly invoked as `/run-attempt` or when the user
asks to start an existing attempt for live interactive review.

## Goal

Start the PsyNet experiment stored in an existing challenge attempt, open the
live experiment dashboard/develop page in the Cursor Desktop browser or remote
desktop, show the dashboard credentials, and leave the server running so the user
can take control there. Do not show local `127.0.0.1` review links in the user
handoff, because they are only useful inside the Cloud Desktop environment. Do
not start or show public links unless the user asks for a tunnel and it has been
created successfully.

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
5. By default, the helper does not start a public tunnel. Watch the output for
   the `Run attempt Cloud Desktop handoff` block. It must include the dashboard
   username and password, but it must not include local participant or dashboard
   review links.
6. Open `http://127.0.0.1:5000/dashboard/develop` in the Cursor Desktop browser
   or remote desktop. If a login form appears, log in automatically with the
   printed username and password. Do not ask the user to perform this login
   manually unless automatic login fails.
7. After login, leave the browser on the dashboard/develop page. Tell the user
   which tmux session is running the server, confirm that Cloud Desktop control
   is ready, and show the credentials. Do not provide local participant or
   dashboard links. Ask whether they would like a public tunnel as well.
8. If the user wants a public tunnel, follow the `public-tunnel` skill for port
   `5000` while keeping the `run-attempt` tmux session running. Watch the tunnel
   output for the public URL. Derive and show:
   - the public participant URL by replacing the local participant URL origin
     with the public tunnel origin;
   - the public dashboard/develop URL by replacing the local dashboard URL
     origin with the public tunnel origin and preserving embedded credentials.

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
- `--public-tunnel` starts Cloudflare Quick Tunnel with the server and prints
  public links once the `trycloudflare.com` URL is available. Use this only when
  the user has already requested a public tunnel. Tunnel setup details are owned
  by the `public-tunnel` skill.
- `--public-tunnel-port <port>` changes the local port exposed when
  `--public-tunnel` is used; PsyNet normally uses `5000`.

## Common failures

- Attempts without `code/**/experiment.py` are not runnable through this skill.
- If multiple experiment directories exist, ask the user which one to run.
- Missing or stale PsyNet dependencies should be fixed in the Cloud Agent
  environment, not by editing the attempt code during this workflow.
- If PsyNet starts but generated commands cannot find runtime tools such as
  `flask`, `--psynet-command /home/ubuntu/PsyNet/.venv/bin/psynet` alone may
  not be enough because PsyNet's generated `run.sh` resolves tools from `PATH`.
  Relaunch the tmux command with the PsyNet virtualenv first on `PATH`, for
  example:
  `tmux -f /exec-daemon/tmux.portal.conf new-session -d -s run-attempt -c "$PWD" -- bash -lc 'export PATH="/home/ubuntu/PsyNet/.venv/bin:$PATH"; uv run python .cursor/skills/run-attempt/scripts/run_attempt.py <attempt> --psynet-command /home/ubuntu/PsyNet/.venv/bin/psynet'`
- If a requested public tunnel produces no URL, follow the failure handling in
  the `public-tunnel` skill. If no tunnel produces a URL, report that public
  tunnel creation is blocked and use Cloud Desktop control instead.
- Use only local, ephemeral dashboard credentials. Do not add real service
  credentials just to make a review run succeed.
