---
name: preview-dashboard-live
description: Start a live Hugo dashboard preview and expose it through a temporary public tunnel for active branch review.
authors: [pmcharrison]
---

# Preview dashboard live

Use this skill when a user wants to review dashboard, documentation, skill, or
challenge-attempt page changes from a Cursor Cloud Agent in a normal web
browser.

This skill starts the local Hugo dashboard server. It then uses the
`public-tunnel` skill to expose that server through a temporary public HTTPS URL.

## Workflow

1. Export current dashboard data:
   `uv run psynetsk-export-dashboard-data`
2. Start Hugo in its own tmux session:
   `tmux -f /exec-daemon/tmux.portal.conf new-session -d -s dashboard-live-preview -- hugo server --source dashboard --bind 0.0.0.0 --port 1313 --baseURL http://127.0.0.1:1313/`
3. Verify the local dashboard responds:
   `curl -I --max-time 10 http://127.0.0.1:1313/`
4. Follow the `public-tunnel` skill for port `1313`.
5. Verify the public tunnel URL:
   `curl -I --max-time 20 <public-url>`
6. Give the user the public URL and the tmux session names:
   - `dashboard-live-preview`
   - `<name>-public-tunnel`
7. Say clearly that the URL is temporary and dies when the tunnel process or VM
   stops.

## Use with pull requests

Use live dashboard previews for active Cursor Cloud review. If a pull request
exists, also follow `dashboard-preview-links` and provide the durable GitHub
Pages PR preview URL plus the branch-filtered workflow status link. Tell the
user that live tunnel URLs may expire when the agent goes to sleep and can be
refreshed on request, while PR previews may take a few minutes to build.

Use this handoff template, omitting links that are not available:

**Links**

- [Plan]({live-dashboard-url})
- [Experiment participant link]({participant-url})
- [Experiment dashboard]({dashboard-url-with-credentials})

*These temporary links will fail once the agent goes to sleep. In that case, you
can ask for new links, or use the [backup dashboard preview]({pr-preview-url}).*

Use a concise first-link label that matches the live dashboard target, such as
`Plan`, `Attempt`, or `Dashboard`.

If no live tunnel is available, share the durable PR preview URL and
branch-filtered workflow link from `dashboard-preview-links`.

To publish your changes, merge the pull request.

## Safety

- Do not commit `public/`; Hugo writes it only for static builds.
- Do not expose a dashboard unless the user asked for a public URL.
- Do not add real service credentials to make a preview work.
