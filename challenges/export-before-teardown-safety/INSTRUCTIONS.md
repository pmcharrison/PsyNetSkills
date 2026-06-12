---
title: Export-before-teardown safety plan
type: experiment operations
difficulty: 7
authors: [ww577]
---

Given the deployment inventory in `references/experiment/active-deployments-snapshot.md`,
produce a safe export-before-teardown plan.

The plan should help a human avoid destroying a PsyNet app or terminating an EC2
server before data has been exported.

For each listed deployment, determine or report:

- Experiment folder.
- App name.
- Server name.
- DNS host.
- Region.
- Current known status.
- Export command.
- Expected export path.
- Evidence that export already exists, if any.
- Destroy app command.
- EC2 teardown command.
- Final verification command.
- Blockers or uncertainties requiring human confirmation.

Order the plan so that exports are verified before any destructive command is
suggested. Group deployments by region when listing EC2 verification commands.

Do not run export, destroy, or teardown commands unless the user explicitly asks.
The default output should be a reviewed command plan with safety checks.

Mark deployments as `ready for teardown`, `export first`, or `needs human
confirmation`.

