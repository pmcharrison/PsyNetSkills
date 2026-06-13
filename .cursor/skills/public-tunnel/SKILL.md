---
name: public-tunnel
description: Start an ephemeral public HTTPS tunnel to a local HTTP service for live review from a browser.
authors: [pmcharrison]
---

# Public tunnel

Use this skill when a user asks to expose a local development server from a
Cursor Cloud Agent through a temporary public URL. This skill owns the generic
tunnel setup only; caller skills still own how to start and validate the local
service.

This skill uses `.cursor/skills/public-tunnel/scripts/public_tunnel.py` to do
the actual tunneling work. The skill file is the agent-facing procedure; the
script is the reusable implementation.

## Goal

Expose a local HTTP service through an ephemeral HTTPS URL without requiring
service credentials, DNS changes, open inbound ports, or a production
deployment.

## Script role

`.cursor/skills/public-tunnel/scripts/public_tunnel.py`:

- chooses `cloudflared`, `localtunnel`, or `npx -y localtunnel`;
- downloads a temporary `/tmp/cloudflared` when needed and supported;
- streams tunnel output and prints a `Public tunnel ready` block when it finds a
  supported public URL;
- exposes URL utilities that caller skills can use to rewrite local links to the
  public tunnel origin.

## Workflow

1. Confirm the local service is already running and responds locally, for
   example:
   `curl -I --max-time 10 http://127.0.0.1:<port>/`
2. Start `.cursor/skills/public-tunnel/scripts/public_tunnel.py` in a separate
   tmux session so the local service keeps running independently:
   `tmux -f /exec-daemon/tmux.portal.conf new-session -d -s <name>-public-tunnel -- uv run python .cursor/skills/public-tunnel/scripts/public_tunnel.py --port <port>`
3. Watch that tmux session for the script's `Public tunnel ready` block and copy
   the public URL.
4. Verify the public URL before handing it to the user:
   `curl -I --max-time 20 <public-url>`
5. Tell the user the public URL, the local service session, and the tunnel
   session. Make clear that the URL is temporary and dies when the VM or tunnel
   process stops.

## Script usage

Run from the repository root:

`uv run python .cursor/skills/public-tunnel/scripts/public_tunnel.py --port <port>`

Useful options:

- `--local-host <host>` changes the local host exposed by the tunnel; default is
  `127.0.0.1`.
- `--print-command` prints the selected tunnel command without starting it.

## Common failures

- If no public URL appears, inspect the script output first. It reports when no
  supported tunnel command is available or when Cloudflare setup falls back to
  another provider.
- Quick Tunnel URLs are accountless and temporary. Do not use them for
  production deployment, durable review archives, or links that must survive
  agent teardown.
- Do not add real service credentials to make a local preview work. If the
  service itself requires credentials, use only local ephemeral development
  credentials and avoid publishing secrets in the public URL unless the caller
  skill explicitly owns that handoff.
