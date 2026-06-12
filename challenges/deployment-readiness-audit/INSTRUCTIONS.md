---
title: Deployment readiness audit
type: experiment operations
difficulty: 5
authors: [ww577]
---

Audit the mock PsyNet experiment dossier in `references/experiment/mock-experiment/` for
deployment readiness and produce a concise readiness report.

Treat the files in `references/experiment/mock-experiment/` as a copied experiment folder.
Inspect the dossier and report whether it appears ready for local debug,
Hotair/internal preview, and eventual recruiter deployment.

The report should check:

- Whether `experiment.py`, `config.txt`, `requirements.txt`, `constraints.txt`,
  `Dockerfile`, `Dockertag`, and `.gitignore` are present when expected.
- Whether dependency installation should use `constraints.txt`.
- Whether `.venv/`, `.deploy/`, `.pytest_cache/`, `exports/`, `deploy_logs/`,
  generated source archives, and logs are excluded from the deployable package.
- Whether assets, manifests, qualification files, recruiter files, and consent
  files are present and deployable.
- Whether any symlinks or hardcoded paths point outside the experiment folder.
- Whether app names, server names, DNS hosts, Docker tags, and study titles look
  stale or copied from another experiment.
- Whether a deployment record, such as `DEPLOYMENT_LOG.md`, contains enough
  metadata for provision, deploy, export, destroy, and teardown. If no such
  record exists, recommend creating one.
- Whether any real credentials, tokens, keys, private paths, or participant data
  appear in files that would be committed or published.

Do not deploy the experiment, run paid recruitment, destroy apps, or teardown
servers. If commands are useful, generate them as recommendations only.

The report should list blockers first, then warnings, then suggested next
actions. It should distinguish facts visible in the dossier from uncertain
inferences.

