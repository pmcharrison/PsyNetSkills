# Deploying PsyNet attempts with human approval

This repository includes a gated `deploy-attempt` workflow for publishing a
PsyNet attempt to an EC2 instance with Dallinger/PsyNet SSH deployment.

The intended safety boundary is:

1. An agent or developer can trigger a dry run or queue a deployment request.
2. GitHub runs the non-privileged `prepare` job and writes a deployment plan.
3. The privileged `deploy` job waits on the protected `attempt-deploy`
   Environment.
4. A human reviewer approves the Environment in GitHub.
5. Only then can the job request a GitHub OIDC token, assume the AWS IAM role,
   reconstruct the SSH private key from Environment secrets, provision EC2, and
   deploy the experiment.

Agents should not have AWS credentials, GitHub Environment admin rights, or
membership in the required reviewer team.

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
3. Add required reviewers and enable prevent self-review.
4. Add the Environment variables printed by the setup script:
   `ATTEMPT_DEPLOY_AWS_ROLE_ARN`, `ATTEMPT_DEPLOY_AWS_REGION`, and
   `ATTEMPT_DEPLOY_SSH_KEY_NAME`.
5. Add the Environment secrets:
   `ATTEMPT_DEPLOY_SSH_PRIVATE_KEY`, `ATTEMPT_DEPLOY_DASHBOARD_USER`, and
   `ATTEMPT_DEPLOY_DASHBOARD_PASSWORD`.

The setup script creates an IAM role whose trust policy accepts GitHub OIDC
tokens only for the protected Environment subject:
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
prints the workflow run URL for human approval. If dispatch is unavailable, it
prints the exact workflow inputs for a human to paste into GitHub.

If dispatch fails with `Resource not accessible by integration`, the GitHub
identity running the helper lacks Actions/workflows write permission for
`workflow_dispatch`. This is separate from AWS credentials and the protected
Environment gate. The fix is either to let a human run the workflow in GitHub,
or to configure a dispatch-only GitHub App/token that can start workflow runs
but is not allowed to approve the `attempt-deploy` Environment.

The `Deploy PsyNet attempt` workflow accepts:

- `attempt_ref`: commit SHA or branch containing the attempt code.
- `attempt_path`: relative path to the PsyNet experiment folder.
- `app_name`: Dallinger/PsyNet app name.
- `server_name`: EC2 instance name.
- `dns_host`: Route53 host to publish; it must match
  `<label>.cursor.cap-experiments.com`.
- `region`, `instance_type`, `storage_gb`, and `security_group_name`.
- `dry_run`: keep `true` to only generate a plan; set `false` to request
  human approval for a real deployment.

Agents can safely trigger this workflow on `main` with `dry_run=false` because
the AWS-capable job remains blocked until a required human reviewer approves
the protected Environment. The user-facing handoff link is the workflow run page;
the reviewer opens it, clicks `Review deployments`, selects `attempt-deploy`,
and approves or rejects.

## Why provision then deploy works

`dallinger ec2 provision` is slow, but it can run in the same GitHub Actions job
as `psynet deploy ssh`. This matters because Dallinger's EC2 provision command:

- requires a local `~/.ssh/<ec2_default_pem>.pem` private key;
- requires `server_pem` in Dallinger config;
- imports the matching public key into EC2 if the key pair is missing;
- launches the instance with that key pair;
- prepares Docker on the new host; and
- stores the DNS host in Dallinger's configured host list.

The workflow reconstructs the private key from a protected GitHub Environment
secret after human approval, writes `~/.dallingerconfig`, runs
`dallinger ec2 provision`, and then runs `psynet deploy ssh` in the same job.
The private key, Dallinger config, and stored host entry therefore remain
available for the SSH deploy step.

## Operational notes

- Use fresh app/server/DNS names unless a human has confirmed that replacing the
  existing DNS record is safe.
- Keep teardown as a separate protected workflow or manual human operation.
- Record export and teardown commands from the workflow summary before running
  paid recruitment.
- Do not store AWS access keys in GitHub or Cursor Cloud; the deploy job uses
  short-lived AWS STS credentials obtained through OIDC after approval.
