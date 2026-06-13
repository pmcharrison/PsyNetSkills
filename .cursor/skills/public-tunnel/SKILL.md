---
name: public-tunnel
description: Start an ephemeral public HTTPS tunnel to a local HTTP service for live review from a browser.
authors: [pmcharrison]
---

# Public tunnel

Use this skill when a user asks to expose an already-running local HTTP service
from Cursor Cloud through a temporary public HTTPS URL.

This skill does not start the app. Caller skills start and validate the local
service. This skill only starts and verifies the tunnel.

## Script used by this skill

Run `.cursor/skills/public-tunnel/scripts/public_tunnel.py`.

That script:

- chooses `cloudflared`, `localtunnel`, or `npx -y localtunnel`;
- downloads temporary `/tmp/cloudflared` if needed;
- starts the tunnel to `http://127.0.0.1:<port>`;
- prints `Public tunnel ready` when it detects the public URL;
- provides URL helpers for caller scripts such as `run-attempt`.

## Workflow

1. Confirm the local service is already running:
   `curl -I --max-time 10 http://127.0.0.1:<port>/`
2. Start the script in its own tmux session:
   `tmux -f /exec-daemon/tmux.portal.conf new-session -d -s <name>-public-tunnel -- uv run python .cursor/skills/public-tunnel/scripts/public_tunnel.py --port <port>`
3. Watch that session for `Public tunnel ready`.
4. Verify the public URL:
   `curl -I --max-time 20 <public-url>`
5. Give the user the public URL and the tmux session names.
6. Say clearly that the URL is temporary and dies when the tunnel process or VM
   stops.

## Caller responsibilities

- `preview-dashboard-live` should start Hugo first.
- Experiment-preview skills should start PsyNet first.
- Caller skills decide whether to rewrite local links, include dashboard
  credentials, or expose participant links.

## Safety

- Do not use this for production deployment or durable review archives.
- Do not add real service credentials.
- Do not expose a service unless the user asked for a public URL.
