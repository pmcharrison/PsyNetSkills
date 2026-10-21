# Deployment Lifecycle Monitoring and Export Plan

## Summary of mock deployment dossier

This plan covers the fictional **Mock Echo Span Pilot** deployment for the experiment folder `experiments/mock_echo_span`. The mock app is `mock-echo-span-pilot-app`, hosted on the mock server `mock-psynet-lab-server-07`, with recruitment through `mock-recruiter-sandbox`. The pilot target was 8 mock participants and is complete; the full target is 120 mock participants and is not approved yet. The mock recruiter is paused, the dashboard reports the app responding with no participants currently in progress, recent logs show no repeated worker crashes, the latest regular export passed sanity checks, and a final export has not yet been completed.

This is a reviewed written plan only. It names command families and review gates for a future operator, but it must not be used as evidence that live deployment, export, recruiter, SSH, cloud, destroy, credential, or teardown commands have been run.

## Lifecycle checklist

### 1. Design and preflight checks before deployment

**Purpose:** Confirm the experiment, recruitment configuration, export path, monitoring surfaces, and teardown targets are internally consistent before any live operation.

**Operator checks:**
- Confirm the experiment folder is `experiments/mock_echo_span` and contains the expected PsyNet files, recruiter configuration, local assets, `.gitignore`, constraints, and deployment record.
- Confirm the app name `mock-echo-span-pilot-app`, server name `mock-psynet-lab-server-07`, recruiter `mock-recruiter-sandbox`, dashboard URL, Dozzle URL, deployment-monitor URL, and export folder `mock_exports/mock_echo_span/` all refer to the same mock deployment.
- Review any code or configuration changes since the pilot, especially consent, recruitment, qualification, payment, trial count, and bonus logic.
- Review the candidate command families without executing them: local debug, bot tests, deployment, export, recruiter pause/stop, `psynet destroy ssh`, and `dallinger ec2 teardown`.

**Evidence safe to proceed:**
- A clean deployment record maps the same app/server/recruiter/export targets through all lifecycle phases.
- No unresolved stale app names, broken local paths, missing assets, or conflicting recruiter settings remain.
- A human operator approves the command names and confirms the final export gate remains mandatory before destruction.

**Block progress if:**
- App, server, recruiter, dashboard, log, monitor, or export identifiers do not match.
- Real credentials or non-mock participant data are required to review the plan.
- The experiment changed after the pilot but local debug and bot testing have not been repeated.

### 2. Local debug testing

**Purpose:** Verify the current experiment can run locally before any deployment or redeployment decision.

**Operator checks:**
- Run only in a safe local environment when authorized, using a command family such as `psynet debug local` from `experiments/mock_echo_span`.
- Exercise consent, instructions, refresh behavior, task trials, completion, and error pages.
- Check local dashboard state and local server logs for uncaught exceptions, repeated reload loops, asset failures, and payment/completion errors.

**Evidence safe to proceed:**
- The full local participant flow completes after the latest code/configuration revision.
- The consent refresh warning from earlier bot testing is either resolved or explicitly accepted with a mitigation.
- Logs show no repeated server, worker, asset, or database errors.

**Block progress if:**
- Any participant path cannot complete locally.
- The local run uses stale code, stale constraints, or a different folder from `experiments/mock_echo_span`.
- Logs contain repeated exceptions, timeout loops, or missing-asset errors.

### 3. Bot testing

**Purpose:** Catch automated-flow regressions and timing problems before recruiting humans.

**Operator checks:**
- Repeat bot testing after any code or configuration change; the dossier's earlier 12 mock bot sessions are not enough after a revision.
- Use a command family such as `psynet test local` or an approved bot-test equivalent.
- Inspect bot logs for consent refresh failures, timeouts, failed completions, duplicate participants, or unexpected trial counts.

**Evidence safe to proceed:**
- The target bot run completes with expected counts and no unresolved timeout pattern.
- Any single transient bot failure has a documented cause and does not affect human participant safety or data completeness.
- Basic dashboard state and logs remain stable during and after the bot run.

**Block progress if:**
- More than a clearly explained transient bot failure occurs.
- Bot results do not match expected study counts or completion states.
- Consent refresh, page reload, or timing failures reproduce.

### 4. Pilot launch checks

**Purpose:** Confirm the completed pilot can support a decision about full-launch readiness without losing pilot data.

**Operator checks:**
- Verify the recruiter remains paused after reaching the mock pilot target of 8 participants.
- Review dashboard state for completed, failed, in-progress, and unpaid participants.
- Review Dozzle/log state for repeated worker crashes, HTTP 500s, task exceptions, export errors, and payment/recruiter callbacks.
- Review the deployment monitor for uptime, recent error count, restart count, and any alert history.
- Check that the latest regular export `mock_exports/mock_echo_span/export_2026-06-01T120000Z.zip` is present and the corresponding sanity check passed.

**Evidence safe to proceed:**
- Pilot completion counts, dashboard state, `basic_data`, and sanity-check outputs agree.
- No active mock participants are in progress.
- No unresolved log or monitor errors affect data integrity, payment, or recruitment.

**Block progress if:**
- Pilot data are not exported or the export sanity check cannot be reproduced.
- The recruiter is still admitting participants unexpectedly.
- Dashboard, log, deployment-monitor, and export counts disagree without explanation.

### 5. Live deployment readiness

**Purpose:** Decide whether the app can move from pilot-complete state to full launch without unsafe recruitment or data-handling risk.

**Operator checks:**
- Confirm full launch has explicit human approval; the dossier says it is not yet approved.
- Re-run local debug and bot tests after any post-pilot change.
- Review the dashboard, Dozzle/logs, deployment monitor, latest export, and sanity-check script together.
- Confirm the full target is 120 mock participants and that recruiter limits, eligibility, and pause/stop controls match that target.
- Prepare a rollback/recruiter-pause plan and identify who can execute it.

**Evidence safe to proceed:**
- Human approval is recorded, local and bot evidence are fresh, the pilot export is healthy, and monitoring surfaces are reachable.
- Recruitment settings are capped for the intended full sample and do not conflict with pilot-complete state.
- Operators know which mock commands would pause recruitment and which would inspect logs/exports.

**Block progress if:**
- Full launch approval is absent.
- Final deployment identifiers or recruiter settings are ambiguous.
- Fresh validation was skipped after a change.

### 6. Ongoing monitoring

**Purpose:** Detect participant-impacting failures, data-quality problems, and infrastructure instability early during recruitment.

**Operator checks:**
- Dashboard: review participant inflow, in-progress count, completion count, failed/error count, payment state, recruitment state, and whether the app is responding.
- Dozzle/logs: scan for repeated worker crashes, task exceptions, database errors, HTTP 500s, asset failures, recruiter callbacks, export errors, and deployment restarts.
- Deployment monitor: check uptime, recent error count, response health, restart count, and alert status.
- `basic_data`: when available from exports, compare participant count, completion rate, trial count distribution, missingness, timing outliers, and bonus/payment fields against expected values.

**Evidence safe to continue:**
- Counts increase at a plausible rate, failures remain isolated and explained, and logs/monitoring do not show repeated errors.
- `basic_data` summaries agree with dashboard counts and expected study structure.
- Recruiter state matches the intended phase: paused during review, open during approved recruitment, stopped at final termination.

**Block progress if:**
- Repeated worker crashes, callback/payment errors, or trial-count mismatches appear.
- Active participants are stuck or in-progress counts do not clear.
- Dashboard, logs, monitor, and `basic_data` disagree in ways that could indicate missing data.

### 7. Regular exports and sanity checks

**Purpose:** Preserve data throughout recruitment and catch problems before the final export is the only copy.

**Operator checks:**
- Run regular exports at approved milestones, such as after pilot completion, after material fixes, daily during live collection, before changing recruitment state, and before teardown decisions.
- Review an export command family such as `psynet export ssh --app mock-echo-span-pilot-app --server <reviewed mock server DNS> --path <absolute export directory>` only after a human confirms it targets `mock-psynet-lab-server-07` and the approved mock environment.
- Store each export in a timestamped path under `mock_exports/mock_echo_span/`, preserve the original archive, and record the command, operator, app, server, timestamp, output path, checksum, and sanity-check result.
- Run an `export.py`-style sanity check or equivalent analysis script on each export before relying on it.

**Sanity-check requirements:**
- Verify expected participant, trial, completion, failed, and in-progress counts.
- Verify obvious data-quality problems: missing core columns, duplicate participants, impossible trial counts, extreme timing outliers, invalid responses, and missing payment/completion status.
- Compare `basic_data` summaries with dashboard counts and deployment-monitor context.
- Produce a concise pass/fail note for each export and keep failed exports for diagnosis without treating them as final evidence.

**Evidence safe to proceed:**
- The latest export archive exists, has a recorded checksum, and passes the sanity check.
- Dashboard counts, `basic_data`, and export analysis agree within documented expectations.

**Block progress if:**
- Export fails, writes to an unexpected path, lacks a checksum, or fails sanity checks.
- The operator cannot confirm which app/server produced the export.
- Export analysis shows missing participants, missing trials, or unexpected completion-rate drops.

### 8. Final export

**Purpose:** Create the last verified data copy before any destructive action.

**Operator checks:**
- Pause or stop recruitment first if needed to prevent new participants from entering during final export review.
- Confirm no active participants are in progress on the dashboard.
- Run the reviewed export command family for `mock-echo-span-pilot-app` into a new timestamped final-export directory under `mock_exports/mock_echo_span/`.
- Run the same `export.py`-style sanity check and compare final counts to dashboard, `basic_data`, and deployment-monitor history.
- Record export path, checksum, app, server, timestamp, command family, operator review, and pass/fail outcome.

**Evidence safe to proceed:**
- Final export exists, is readable, has a checksum, and passes completeness/data-quality checks.
- Dashboard shows no in-progress participants and counts agree with final export analysis.
- A human operator signs off that this export is the authoritative final copy.

**Block progress if:**
- Final export is missing, fails, or has not been sanity checked.
- Participants are still active or recruiter state is uncertain.
- Any count mismatch could indicate data loss.

### 9. Recruitment termination or pause

**Purpose:** Stop or pause participant entry before app destruction, redeployment, or server teardown.

**Operator checks:**
- Confirm whether the desired action is temporary pause, permanent stop, or no action because recruitment is already closed.
- Verify recruiter `mock-recruiter-sandbox` status directly in the approved recruiter interface or command family.
- Confirm dashboard has no active mock participants and that recent callbacks/payments have settled.
- Record the recruiter state before and after the action.

**Evidence safe to proceed:**
- Recruiter is paused or stopped as intended, and no new participants can enter.
- Dashboard in-progress count is zero and final export remains valid after recruiter state changes.

**Block progress if:**
- Recruiter status cannot be verified.
- Participants are still active or callbacks/payments remain unsettled.
- The operator intends to redeploy/destroy before stopping recruitment.

### 10. Application and server teardown

**Purpose:** Remove only the intended app and server resources after data and recruitment gates are satisfied.

**Operator checks before any destructive command:**
- Confirm final export path, checksum, and sanity-check pass.
- Confirm recruiter paused/stopped and no active participants.
- Confirm the destructive app target is exactly `mock-echo-span-pilot-app` and the server target is exactly `mock-psynet-lab-server-07`.
- Have a human operator review the command family, target names, region/DNS fields, and deployment record.

**App destruction guidance:**
- `psynet destroy ssh --app <app-name> --server <server-dns>` destroys the PsyNet/Dallinger app deployment on the server.
- Review a mock target equivalent for `mock-echo-span-pilot-app` only after final export and recruiter gates pass.
- After destruction, verify the app is no longer listed/responding and record logs or dashboard evidence if available.

**Server teardown guidance:**
- Dallinger EC2 server teardown is a separate action from app destruction.
- A command family such as `dallinger ec2 teardown --name <server-name> --region <region> --dns-host <server-dns>` should be reviewed only after confirming no other apps or studies depend on `mock-psynet-lab-server-07`.
- After teardown, verify the server is removed from the infrastructure inventory and no unexpected resources remain.

**Evidence safe to complete:**
- Final export and recruiter gates passed before destruction.
- App destruction and server teardown are separately reviewed, separately executed, and separately verified.
- Deployment record is updated with final export, recruiter state, destruction result, teardown result, and any blockers.

**Block progress if:**
- Final export is incomplete or unverified.
- Recruiter is not stopped/paused or participants are active.
- App and server names do not match the dossier, or the server may host other work.
- The same command is being treated as both app destruction and EC2 teardown.

## Risk register

| Risk | Prevention in this plan |
| --- | --- |
| Destroying the app before final data export | Final export, checksum, sanity check, and human sign-off are hard gates before `psynet destroy ssh`. |
| Tearing down the EC2 server while other work depends on it | Server teardown is separate from app destruction and requires an inventory/dependency check. |
| Restarting or redeploying while recruitment is open | Recruiter pause/stop and dashboard active-participant checks are required before redeployment or destruction. |
| Relying on stale pilot evidence after code/config changes | Local debug and bot testing must be repeated after every experiment code or configuration change. |
| Missing data-quality problems until final teardown | Regular exports plus `export.py`-style sanity checks compare dashboard, `basic_data`, and expected counts throughout the lifecycle. |
| Confusing mock app/server/recruiter identifiers | Preflight requires all identifiers, URLs, exports, and command targets to match the same mock deployment record. |
| Treating logs as healthy without checking structured data | Monitoring includes dashboard state, Dozzle/logs, deployment-monitor outputs, and `basic_data` or export-derived checks. |
| Executing credential-dependent commands from a written plan | This attempt names command families for human review only and records that no live operations were executed. |
