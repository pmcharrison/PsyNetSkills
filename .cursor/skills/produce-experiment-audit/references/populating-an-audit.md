# Populate an experiment audit

Use this reference whenever populating a PsyNet audit, whether it is a
standalone experiment's `audit/` directory or a challenge attempt whose root is
the audit packet.

Let `AUDIT_ROOT` mean:

- `audit/` for a standalone experiment audit;
- the attempt root for a PsyNetSkills challenge attempt.

## Ownership

Implementation and validation skills **produce** audit artifacts as they run.
This reference owns paths, statuses, blockers, inventory, validate, and render.

Do **not** treat audit population as a second evidence campaign. If
`artifacts/performance.json` (or another required output) is already present
from implementation, mark it present and move on. Re-run an expensive check only
when the existing file is missing, invalid, or no longer represents the final
implementation.

## Early audit-aware habit

Initialize the packet before meaningful runs. From the first useful command
onward, write outputs into the audit layout even when they are interim:

- Prefer canonical paths such as `artifacts/performance.json`,
  `artifacts/simulated_data.zip`, and `analyses/analysis.ipynb`.
- Overwrite the same path when a later run supersedes an interim result.
- Keep smoke-only outputs out of `status: "present"` until they are review-ready;
  leave the artifact `blocked`/`missing` or replace the file before marking
  present.
- Update `audit.json` as files land (`psynet audit mark-present ...`).

## Workflow

1. Initialize the packet before collecting evidence.
   - Standalone: run `psynet audit init` from the experiment directory.
   - Challenge: use the initialization procedure in
     `attempt-challenge/references/challenge-audit-extension.md`.
2. Fill the core section files:
   - `PLAN.md`: implementation plan;
   - `REPORT.md`: implementation, validation, analysis, and limitations;
   - `TIMELINE.md`: notable implementation and evidence events;
   - `PROMPT.md`: original prompt or brief when useful.
3. Collect reviewable outputs under:
   - `artifacts/` for participant flow, exports, monitor snapshots, performance
     results, and other primary evidence;
   - `analyses/` for notebooks and analysis outputs;
   - `logs/` for concise command logs.
4. Keep evidence-generation scripts with the implementation source. Evidence
   should be reproducible, not just a manually assembled folder.
5. After an artifact exists, run:

   ```bash
   psynet audit mark-present <artifact_id> <AUDIT_ROOT>
   ```

   Add a manifest entry first when the artifact is not already declared.
6. Record checks and blockers honestly in `audit.json`. A structurally valid
   packet may still contain blockers.
7. Before handoff, run:

   ```bash
   psynet audit validate <AUDIT_ROOT>
   psynet audit render <AUDIT_ROOT>
   ```

   When the current directory is the audit root, pass `.`. The CLI default is
   `audit/`, which is convenient from a standalone experiment root but is not
   correct from a challenge attempt root.

## Evidence checklist

Choose evidence that matches the experiment. Common artifacts are:

- `artifacts/participant.mp4`: concise participant walkthrough;
- `artifacts/screenshots/*.png`: targeted participant-facing states;
- `artifacts/screenshots/manifest.json`: optional screenshot captions;
- `artifacts/performance.json`: sustained performance-test output;
- `artifacts/monitor.html`: static monitor snapshot;
- `artifacts/data.zip`: exported local or real-run data;
- `artifacts/simulated_data.zip`: simulated-participant export;
- `analyses/analysis.ipynb`: executed, self-contained analysis notebook;
- `logs/*.log`: concise logs that explain commands and failures.

Use `record-participant-video` for screenshot and video production. Keep videos
at most 3 minutes and 1280×720. Keep rendered notebooks small enough for the
dashboard to read (normally under about 100 KB).

For performance evidence, use a sustained test rather than a one-bot smoke test.
Prefer `--audit-dir` so PsyNet writes the canonical audit path:

```bash
# From code/<slug>/ in a challenge attempt
psynet performance-test local \
  --n-bots 40 \
  --duration-minutes 5 \
  --time-factor 1.0 \
  --audit-dir ../..

# Standalone experiment with ./audit/
psynet performance-test local \
  --n-bots 40 \
  --duration-minutes 5 \
  --time-factor 1.0 \
  --audit-dir audit
```

`--audit-dir` writes `<AUDIT_ROOT>/artifacts/performance.json`. Use
`--json-output` only when you need a non-audit path. Prefer an absolute audit
path when PsyNet may execute from a temporary deployment directory.

## Manifest rules

For every review-relevant artifact, declare a stable lowercase snake-case id,
kind, relative path, title, description, whether it is required, status, and
creator.

Use statuses consistently:

- `present`: the declared file exists and is ready to inspect;
- `missing`: no completed artifact exists yet;
- `blocked`: a real attempt failed or cannot proceed;
- `not_applicable`: the experiment design does not need the artifact.

Every required non-present artifact needs a matching blocker. A useful blocker
states what was attempted, what prevented completion, and the next concrete
step. Never turn a skipped or failed check into passing evidence.

Each screenshot intended for display must be declared as an artifact; a caption
manifest alone does not publish the images.

## Analysis and reporting

The canonical analysis is `analyses/analysis.ipynb` unless another format is
more appropriate. It should:

- read exported data directly;
- show data loading and cleaning;
- display useful summary tables or plots;
- distinguish technical validation from scientific conclusions.

`REPORT.md` should state:

- what was implemented;
- which commands and procedures ran;
- where the important evidence lives;
- what export and analysis showed;
- which checks remain blocked, missing, or not applicable;
- how a reviewer can reproduce or extend the checks.

Do not claim an experiment is fully validated unless every required artifact
and check supports that claim.

## Safety

Use only safe local credentials and redact secrets from logs and artifacts.
Never commit production tokens, custom service credentials, or participant
secrets.

When a requirement depends on an external service, collect evidence that the
real integration worked end to end. Mocks and simulated payloads support
development but do not prove the real integration unless the task explicitly
defines simulation as acceptable. If safe access is unavailable, record a
blocker that says exactly what remains unverified.
