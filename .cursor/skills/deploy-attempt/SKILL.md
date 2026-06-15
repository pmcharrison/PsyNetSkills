---
name: deploy-attempt
description: Queue a protected GitHub Actions deployment for a PsyNetSkills attempt, deriving workflow inputs and handing the human reviewer the approval run link.
authors: [lucasgautheron]
---

# Deploy an attempt

Use this skill only when explicitly invoked as `/deploy-attempt` or when the
user asks to deploy an existing PsyNetSkills attempt to the protected EC2
deployment workflow.

## Required reads

- Read `psynet-deployment-ops/SKILL.md` before preparing the request. That skill
  owns deployment readiness, command patterns, credential safety, export
  records, and teardown guidance.
- If the attempt was just created and its structure is unclear, read
  `attempt-challenge/SKILL.md` for the standard attempt layout.

## Safety boundary

- Do not run `dallinger ec2 provision`, `psynet deploy ssh`, AWS CLI deploy
  operations, app destruction, or teardown from the agent shell.
- Do not request, inspect, print, copy, or store AWS credentials, `.env`,
  `.dallingerconfig`, dashboard passwords, SSH private keys, or recruiter
  tokens.
- The agent may queue the GitHub Actions workflow. The protected
  `attempt-deploy` Environment must remain the human approval gate.
- Never approve the deployment Environment, bypass protection rules, add the
  agent to required reviewers, or alter GitHub Environment settings.

## Workflow

1. Resolve the attempt or experiment path. Accept:
   - `challenges/<challenge>/attempts/<attempt>`;
   - an experiment directory containing `experiment.py` and `config.txt`;
   - `<challenge>/<attempt>` when it maps to a standard attempt folder;
   - the current directory if it is inside one of those paths.
2. Run the helper in plan mode first:
   `python3 .cursor/skills/deploy-attempt/scripts/deploy_attempt.py <attempt>`
3. Check the derived values:
   - `attempt_ref`: current `git rev-parse HEAD`;
   - `attempt_path`: relative experiment directory;
   - `app_name` and `server_name`: deterministic slug from challenge/attempt and
     commit;
   - `dns_host`: `<slug>.cursor.cap-experiments.com`;
   - `dry_run`: `false` only when the user requested a real deploy request.
4. If the user invoked `/deploy-attempt` and did not ask for plan-only mode,
   queue the protected workflow:
   `python3 .cursor/skills/deploy-attempt/scripts/deploy_attempt.py <attempt> --request-deploy`
5. If the helper returns a workflow run URL, give the user that URL and tell them
   to open it, click `Review deployments`, select `attempt-deploy`, and approve
   or reject.
6. If workflow dispatch is unavailable to the agent, give the user:
   - the workflow URL printed by the helper;
   - the exact inputs printed by the helper;
   - the instruction to run it from `main` with `dry_run=false`.
7. Record in your final response that the agent queued only the protected
   workflow request and did not receive AWS credentials or approve deployment.

## Helper usage

Run from the repository root:

`python3 .cursor/skills/deploy-attempt/scripts/deploy_attempt.py <attempt>`

Useful options:

- `--request-deploy` triggers `workflow_dispatch` with `dry_run=false`.
- `--plan-only` prints a dry-run payload with `dry_run=true`.
- `--experiment-dir <path>` selects the experiment when an attempt contains
  multiple `experiment.py` files.
- `--app-name`, `--server-name`, and `--dns-host` override derived values. Use
  overrides sparingly; `dns_host` must end with `.cursor.cap-experiments.com`.
- `--workflow-ref main` selects the trusted branch that contains
  `.github/workflows/deploy-attempt.yml`.

## Failure modes

- If the helper cannot identify exactly one experiment directory, ask for
  `--experiment-dir`.
- If `gh api` reports insufficient permissions, do not try another credential.
  Provide the printed GitHub workflow URL and inputs for a human to run.
- If names exceed GitHub, DNS, Dallinger, or EC2 limits, shorten only the
  free-form slug prefix; keep the commit suffix for traceability.
- If the workflow run is queued successfully but waits for approval, stop there:
  the wait is the intended safeguard.
