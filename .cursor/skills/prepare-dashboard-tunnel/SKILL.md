---
name: prepare-dashboard-tunnel
description: Start a live Hugo dashboard preview and expose it through a temporary public tunnel for user review.
compatibility: Requires Hugo extended, uv sync, and network access for the public tunnel.
---

# Prepare dashboard tunnel

## Workflow

1. Export current dashboard data:
   `uv run psynetsk-export-dashboard-data`
2. Start Hugo in its own tmux session:
   `tmux -f /exec-daemon/tmux.portal.conf new-session -d -s dashboard-live-preview -- hugo server --source dashboard --bind 0.0.0.0 --port 1313 --baseURL http://127.0.0.1:1313/`
3. Follow the PsyNet skill
   `~/PsyNet/.cursor/skills/experiment/public-tunnel/SKILL.md` for port `1313`
