---
name: prepare-dashboard-tunnel
description: Start a live Hugo dashboard preview and expose it through a temporary public tunnel for user review.
authors: [pmcharrison]
---

# Prepare dashboard tunnel

Use this skill to obtain a temporary public tunnel to the current dashboard build.

## Workflow

1. Export current dashboard data:
   `uv run psynetsk-export-dashboard-data`
2. Start Hugo in its own tmux session:
   `tmux -f /exec-daemon/tmux.portal.conf new-session -d -s dashboard-live-preview -- hugo server --source dashboard --bind 0.0.0.0 --port 1313 --baseURL http://127.0.0.1:1313/`
3. Follow the `public-tunnel` skill for port `1313`
