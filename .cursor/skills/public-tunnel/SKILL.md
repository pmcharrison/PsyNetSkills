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

## Goal

Expose a local HTTP service through an ephemeral HTTPS URL without requiring
service credentials, DNS changes, open inbound ports, or a production
deployment. Prefer Cloudflare Quick Tunnel, and fall back to localtunnel only
when Cloudflare setup is unavailable.

## Workflow

1. Confirm the local service is already running and responds locally, for
   example:
   `curl -I --max-time 10 http://127.0.0.1:<port>/`
2. Start the tunnel in a separate tmux session so the local service keeps
   running independently:
   `tmux -f /exec-daemon/tmux.portal.conf new-session -d -s <name>-public-tunnel -- uv run python .cursor/skills/public-tunnel/scripts/public_tunnel.py --port <port>`
3. Watch the tmux output for the `Public tunnel ready` block and copy the
   `https://...trycloudflare.com` URL.
4. Verify the public URL before handing it to the user:
   `curl -I --max-time 20 <public-url>`
5. Tell the user the public URL, the local service session, and the tunnel
   session. Make clear that the URL is temporary and dies when the VM or tunnel
   process stops.

## Helper usage

Run from the repository root:

`uv run python .cursor/skills/public-tunnel/scripts/public_tunnel.py --port <port>`

Useful options:

- `--local-host <host>` changes the local host exposed by the tunnel; default is
  `127.0.0.1`.
- `--print-command` prints the selected tunnel command without starting it.

## Common failures

- If `cloudflared` is missing, the helper downloads a temporary binary to
  `/tmp/cloudflared` when `curl` and the current CPU architecture are supported.
- If Cloudflare setup fails because downloads or outbound tunnel connections are
  blocked, the helper falls back to `localtunnel` or `npx -y localtunnel` when
  available.
- Quick Tunnel URLs are accountless and temporary. Do not use them for
  production deployment, durable review archives, or links that must survive
  agent teardown.
- Do not add real service credentials to make a local preview work. If the
  service itself requires credentials, use only local ephemeral development
  credentials and avoid publishing secrets in the public URL unless the caller
  skill explicitly owns that handoff.
