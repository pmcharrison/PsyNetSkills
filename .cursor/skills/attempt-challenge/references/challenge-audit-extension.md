# Challenge audit extension

A new challenge attempt uses its **attempt root as the audit packet**. It does
not create a nested `audit/` directory.

## Initialize

From the new attempt root, initialize the challenge audit:

```bash
uv run python - <<'PY'
from pathlib import Path
from psynetsk_tools.challenge_audit import init_challenge_attempt_audit

init_challenge_attempt_audit(Path("."), write_starter_markdown=True)
PY
```

The generated manifest declares:

```json
{
  "profile": "psynet.core",
  "extensions": ["psynetskills.challenge"]
}
```

It also creates `artifacts/`, `analyses/`, and `logs/`. New attempts must not
create the legacy `evidence/` directory.

## Extension contract

The extension adds workshop sections, using only core audit section kinds:

- `challenge`: `challenge/INSTRUCTIONS.md`;
- `evaluation`: `EVALUATION.md`;
- `learnings`: `LEARNINGS.md`;
- `agent_metadata`: `agent.json`;
- `code_files`: implementation files under `code/`;
- `evidence_files`: files under the audit evidence directories;
- `challenge_snapshot`: files under `challenge/`.

Core files such as `PLAN.md`, `REPORT.md`, and `TIMELINE.md` remain at the
attempt root.

Workshop lifecycle rules:

- Snapshot the challenge under `challenge/` without reading hidden criteria
  before implementation and evidence collection.
- Record agent and PsyNet provenance in `agent.json`.
- Keep `ended_at: null` while the attempt is paused or incomplete.
- Initialize and maintain `LEARNINGS.md` and `TIMELINE.md`.
- Leave `EVALUATION.md` for human evaluation unless the user supplies feedback.
- After evidence collection, copy the criteria checklist for evaluation as
  directed by the challenge workflow.

For artifact selection, manifest statuses, blockers, validation, and rendering,
follow the PsyNet reference
`~/PsyNet/.cursor/skills/experiment/produce-experiment-audit/references/populating-an-audit.md`.
Challenge-specific instructions may add artifacts, but should not duplicate or
override the core audit contract.
