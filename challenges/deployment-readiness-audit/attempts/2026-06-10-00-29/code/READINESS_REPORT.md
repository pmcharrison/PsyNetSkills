# Deployment Readiness Report

Audited dossier: `challenges/deployment-readiness-audit/references/mock-experiment`

## Verdict

The dossier is **not ready** for local debug, Hotair/internal preview, or eventual recruiter deployment.

Visible facts support several deployment blockers. Items under uncertain inferences need confirmation against the intended PsyNet deployment template.

## Blockers

- Missing expected deployment files: `constraints.txt`, `.gitignore`. Visible files are `DEPLOYMENT_LOG.md`, `Dockertag`, `README.md`, `config.txt`, `experiment.py`, `requirements.txt`.
- `constraints.txt` is absent, so dependency installation cannot use a locked PsyNet-compatible environment.
- `requirements.txt` points PsyNet at GitLab `master`; deployment should install from generated constraints instead of an unpinned moving branch.
- No `.gitignore` is present, so `.venv/`, `.deploy/`, `.pytest_cache/`, `exports/`, `deploy_logs/`, source archives, and logs are not visibly excluded from the deployable package.
- Hardcoded path(s) point outside the experiment folder: `/Users/researcher/cap.pem`.
- Stale copied identifiers appear across experiment metadata, config, Dockertag, and deployment log: `old-beat-validation-template`, `Old Beat Validation Template`, `Old Workspace`, `Old Beat Validation`, `ww-old-beatval`.
- `dashboard_password` is still a placeholder (`TODO_REPLACE_BEFORE_DEPLOY`); the dossier is not deployable until local dashboard defaults or safe secret handling are chosen.
- The experiment selects the Prolific recruiter, but no recruiter or qualification JSON files are visible in the dossier.
- `DEPLOYMENT_LOG.md` exists but is not sufficient for recovery; it lacks metadata or commands for `provision`, `dashboard`, `export`, `destroy`, `teardown`, `verification`.
- `DEPLOYMENT_LOG.md` still contains TODO values for server, DNS host, and region.

## Warnings

- No consent file is visible. This may be acceptable only if consent is provided by shared PsyNet defaults or another documented route.
- No asset directory or manifest is visible; confirm the minimal pages do not rely on local media or generated manifests.
- Local debug and deploy status are explicitly not recorded or not run.
- No symlinks are visible in the dossier.
- No obvious AWS keys, private-key blocks, Prolific API tokens, or participant data were detected by pattern scan.

## Uncertain inferences

- `Dockertag` is present but `Dockerfile` is absent. Some PsyNet deployment templates may not need a custom Dockerfile; confirm against the target template before treating this as fatal.
- The dossier has only a minimal PsyNet timeline, so local debug readiness cannot be inferred without adding constraints and running `psynet debug local`.

## Suggested next actions

1. Create `constraints.txt` from the intended PsyNet environment and install with `uv pip install -r constraints.txt`.
2. Add `.gitignore` entries for `.venv/`, `.deploy/`, `.pytest_cache/`, `exports/`, `deploy_logs/`, `*.tar.gz`, `*.zip`, `*.log`.
3. Replace stale app, server, DNS, Docker tag, Prolific workspace/project, and study title values with the real study identifiers.
4. Remove hardcoded private paths such as `server_pem = /Users/researcher/cap.pem`; document safe local setup outside committed files.
5. Add or document recruiter, qualification, consent, and asset/manifest files needed for the selected recruiter and participant flow.
6. Expand `DEPLOYMENT_LOG.md` with provision, deploy, dashboard/log, export path, destroy, EC2 teardown, and final verification commands.
7. After the dossier is cleaned, run local debug first; only then prepare Hotair/internal preview and recruiter deployment commands as recommendations.

