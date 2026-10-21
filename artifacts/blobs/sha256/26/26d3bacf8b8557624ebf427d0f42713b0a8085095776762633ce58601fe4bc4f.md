---
title: Deployment record reconstruction
type: experiment operations
difficulty: 6
authors: [williambotticelli-wells]
---

Reconstruct a PsyNet deployment record from the messy deployment dossier in
`references/messy-deployment-dossier.md`.

The dossier contains partial deployment notes, shell snippets, export folder
names, config fragments, app names, server names, DNS hosts, and deployment
artifacts. Your task is to infer the deployment state and produce a clean
deployment record. Use `DEPLOYMENT_LOG.md` as the target filename and format,
but understand this as a workshop/lab best practice rather than a required
PsyNet core file.

The reconstructed log should include:

- Experiment folder path.
- App name or candidate app names.
- Server name.
- DNS host.
- AWS region or internal server if inferable.
- Instance type if inferable.
- Recruiter and qualification/config files if inferable.
- Provision command if inferable.
- Deploy command if inferable.
- Dashboard and log URLs if inferable.
- Export commands and export paths.
- Whether exports appear complete, partial, missing, or unknown.
- Destroy and teardown commands, clearly marked as commands not to run without
  human approval.
- Unknowns and conflicts that need human confirmation.

Do not invent missing deployment facts. Mark uncertain values as `TODO` or
`candidate`. Do not run deployment, export, destroy, or teardown commands unless
the user explicitly asks.

The final answer should include the reconstructed log and a short section called
`Unresolved questions`.

