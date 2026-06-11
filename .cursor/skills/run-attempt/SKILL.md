---
name: run-attempt
description: Start a runnable PsyNet challenge attempt with psynet debug local for interactive review through Cursor/browser port forwarding.
authors: [pmcharrison]
disable-model-invocation: true
---

# Run an attempt

Use this skill only when explicitly invoked as `/run-attempt` or when the user
asks to start an existing attempt for live interactive review.

## Goal

Start the PsyNet experiment stored in an existing challenge attempt and report
the participant/ad URL that reviewers can open from the Cursor browser or a
forwarded local port.

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
5. Watch the output for the generated PsyNet ad/participant URL and report it to
   the user. Also tell them which terminal/tmux session is running the server.
6. If Cursor forwards the port, tell the user they can open the forwarded URL
   from their browser. If no forwarded browser URL is available, use the Cursor
   browser or remote desktop inside the agent context.

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

## Common failures

- Attempts without `code/**/experiment.py` are not runnable through this skill.
- If multiple experiment directories exist, ask the user which one to run.
- Missing or stale PsyNet dependencies should be fixed in the Cloud Agent
  environment, not by editing the attempt code during this workflow.
- Do not add real service credentials just to make a review run succeed.
