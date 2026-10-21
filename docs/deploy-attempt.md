# Deploying PsyNet attempts

This repository includes a `deploy-attempt` workflow for publishing a PsyNet
attempt to an EC2 instance with Dallinger/PsyNet SSH deployment.

The current setup is:

1. An agent or developer can trigger a dry run or queue a deployment request.
2. GitHub runs the non-privileged `prepare` job and writes a deployment plan.
3. If `dry_run=false`, the `deploy` job uses the `attempt-deploy` Environment
   variables/secrets, requests a GitHub OIDC token, assumes the AWS IAM role,
   reconstructs the SSH private key from Environment secrets, provisions EC2,
   and deploys the experiment.

Agents should not have AWS credentials or GitHub Environment admin rights. Any
identity that can dispatch the workflow can start a real EC2 deployment, so
dispatch permission should be limited to trusted automation or humans.

## One-time setup

1. Run the AWS bootstrap script from a trusted local machine that has AWS CLI
   credentials with permission to create IAM roles and policies:

   ```bash
   .github/scripts/setup-attempt-deploy-aws.sh \
     --github-repository pmcharrison/PsyNetSkills \
     --hosted-zone-id Z1234567890ABC \
     --regions us-east-1 \
     --generate-ssh-key
   ```

2. In GitHub, create an Environment named `attempt-deploy`.
3. Add the Environment variables printed by the setup script:
   `ATTEMPT_DEPLOY_AWS_ROLE_ARN`, `ATTEMPT_DEPLOY_AWS_REGION`, and
   `ATTEMPT_DEPLOY_SSH_KEY_NAME`.
4. Add the Environment secrets:
   `ATTEMPT_DEPLOY_SSH_PRIVATE_KEY`, `ATTEMPT_DEPLOY_DASHBOARD_USER`, and
   `ATTEMPT_DEPLOY_DASHBOARD_PASSWORD`.

The setup script creates an IAM role whose trust policy accepts GitHub OIDC
tokens only for the `attempt-deploy` Environment subject:
`repo:OWNER/REPO:environment:attempt-deploy`.

## Running a deployment request

Agents should not ask users to type these values manually. Use the helper from
the `/deploy-attempt` skill to derive defaults:

```bash
python3 .cursor/skills/deploy-attempt/scripts/deploy_attempt.py <attempt>
```

To queue a real deployment request, the agent runs:

```bash
python3 .cursor/skills/deploy-attempt/scripts/deploy_attempt.py <attempt> --request-deploy
```

The helper triggers the workflow when its GitHub token has permission, then
prints the workflow run URL. If dispatch is unavailable, it
prints the exact workflow inputs for a human to paste into GitHub.

If dispatch fails with `Resource not accessible by integration`, the GitHub
identity running the helper lacks Actions/workflows write permission for
`workflow_dispatch`. This is separate from AWS credentials. The fix is either
to let a human run the workflow in GitHub, or to configure a dispatch-capable
GitHub App/token.

The `Deploy PsyNet attempt` workflow accepts:

- `attempt_ref`: commit SHA or branch containing the attempt code.
- `attempt_path`: relative path to the PsyNet experiment folder.
- `app_name`: Dallinger/PsyNet app name.
- `server_name`: EC2 instance name.
- `dns_host`: Route53 host to publish; it must match
  `<label>.cursor.cap-experiments.com`.
- `region`, `instance_type`, `storage_gb`, and `security_group_name`.
- `dry_run`: keep `true` to only generate a plan; set `false` to run a real
  deployment.

The user-facing handoff link is the workflow run page. The deploy job starts
automatically once the prepare job succeeds.

## Why provision then deploy works

`dallinger ec2 provision` is slow, but it can run in the same GitHub Actions job
as `psynet deploy ssh`. This matters because Dallinger's EC2 provision command:

- requires a local `~/.ssh/<ec2_default_pem>.pem` private key;
- requires `server_pem` in Dallinger config;
- imports the matching public key into EC2 if the key pair is missing;
- launches the instance with that key pair;
- prepares Docker on the new host; and
- stores the DNS host in Dallinger's configured host list.

The workflow reconstructs the private key from a GitHub Environment secret,
writes `~/.dallingerconfig`, runs `dallinger ec2 provision`, and then runs
`psynet deploy ssh` in the same job. The private key, Dallinger config, and
stored host entry therefore remain available for the SSH deploy step.

## Operational notes

- Use fresh app/server/DNS names unless a human has confirmed that replacing the
  existing DNS record is safe.
- Keep teardown as a separate controlled workflow or manual human operation.
- Record export and teardown commands from the workflow summary before running
  paid recruitment.
- Do not store AWS access keys in GitHub or Cursor Cloud; the deploy job uses
  short-lived AWS STS credentials obtained through OIDC during the deploy run.
