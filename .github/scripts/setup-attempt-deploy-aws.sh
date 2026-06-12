#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage:
  setup-attempt-deploy-aws.sh \
    --github-repository OWNER/REPO \
    --hosted-zone-id ZONE_ID \
    [--environment attempt-deploy] \
    [--role-name PsyNetSkillsAttemptDeploy] \
    [--regions us-east-1,us-east-2] \
    [--ssh-key-name psynetskills-attempt-deploy] \
    [--ssh-private-key-path ~/.ssh/psynetskills-attempt-deploy.pem] \
    [--generate-ssh-key]

Creates or updates the AWS OIDC provider, IAM role, and inline policy used by
.github/workflows/deploy-attempt.yml. It does not configure GitHub Environment
reviewers or secrets; those must be configured in GitHub by a repository admin.
EOF
}

github_repository=""
environment_name="attempt-deploy"
role_name="PsyNetSkillsAttemptDeploy"
regions="us-east-1"
hosted_zone_id=""
ssh_key_name="psynetskills-attempt-deploy"
ssh_private_key_path=""
generate_ssh_key=false
oidc_subject=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --github-repository)
      github_repository="${2:-}"
      shift 2
      ;;
    --environment)
      environment_name="${2:-}"
      shift 2
      ;;
    --role-name)
      role_name="${2:-}"
      shift 2
      ;;
    --regions)
      regions="${2:-}"
      shift 2
      ;;
    --hosted-zone-id)
      hosted_zone_id="${2:-}"
      shift 2
      ;;
    --ssh-key-name)
      ssh_key_name="${2:-}"
      shift 2
      ;;
    --ssh-private-key-path)
      ssh_private_key_path="${2:-}"
      shift 2
      ;;
    --generate-ssh-key)
      generate_ssh_key=true
      shift
      ;;
    --oidc-subject)
      oidc_subject="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [ -z "${github_repository}" ] || [ -z "${hosted_zone_id}" ]; then
  usage
  exit 2
fi

if ! command -v aws >/dev/null 2>&1; then
  echo "aws CLI is required." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required for JSON policy generation." >&2
  exit 1
fi

account_id="$(aws sts get-caller-identity --query Account --output text)"
oidc_provider_arn="arn:aws:iam::${account_id}:oidc-provider/token.actions.githubusercontent.com"
role_arn="arn:aws:iam::${account_id}:role/${role_name}"
hosted_zone_id="${hosted_zone_id#/hostedzone/}"
hosted_zone_arn="arn:aws:route53:::hostedzone/${hosted_zone_id}"

if [ -z "${oidc_subject}" ]; then
  oidc_subject="repo:${github_repository}:environment:${environment_name}"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT
trust_policy="${tmp_dir}/trust-policy.json"
permissions_policy="${tmp_dir}/permissions-policy.json"

python3 - "$trust_policy" "$oidc_provider_arn" "$oidc_subject" <<'PY'
import json
import sys

path, provider_arn, oidc_subject = sys.argv[1:4]
policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Federated": provider_arn},
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                    "token.actions.githubusercontent.com:sub": oidc_subject,
                }
            },
        }
    ],
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(policy, f, indent=2)
    f.write("\n")
PY

python3 - "$permissions_policy" "$regions" "$hosted_zone_arn" <<'PY'
import json
import sys

path, regions_csv, hosted_zone_arn = sys.argv[1:4]
regions = [region.strip() for region in regions_csv.split(",") if region.strip()]
policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ReadEc2State",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeImages",
                "ec2:DescribeInstances",
                "ec2:DescribeInstanceTypes",
                "ec2:DescribeKeyPairs",
                "ec2:DescribeRegions",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeVolumes",
            ],
            "Resource": "*",
            "Condition": {"StringEquals": {"aws:RequestedRegion": regions}},
        },
        {
            "Sid": "ProvisionDallingerEc2",
            "Effect": "Allow",
            "Action": [
                "ec2:AuthorizeSecurityGroupIngress",
                "ec2:CreateSecurityGroup",
                "ec2:CreateTags",
                "ec2:ImportKeyPair",
                "ec2:ModifyInstanceAttribute",
                "ec2:ModifyVolume",
                "ec2:RunInstances",
            ],
            "Resource": "*",
            "Condition": {"StringEquals": {"aws:RequestedRegion": regions}},
        },
        {
            "Sid": "ReadUbuntuAmiParameter",
            "Effect": "Allow",
            "Action": "ssm:GetParameter",
            "Resource": "*",
            "Condition": {"StringEquals": {"aws:RequestedRegion": regions}},
        },
        {
            "Sid": "ReadRoute53Zones",
            "Effect": "Allow",
            "Action": [
                "route53:GetChange",
                "route53:ListHostedZonesByName",
                "route53:ListResourceRecordSets",
            ],
            "Resource": "*",
        },
        {
            "Sid": "ChangeAttemptHostedZone",
            "Effect": "Allow",
            "Action": "route53:ChangeResourceRecordSets",
            "Resource": hosted_zone_arn,
        },
        {
            "Sid": "AllowEc2ServiceLinkedRole",
            "Effect": "Allow",
            "Action": "iam:CreateServiceLinkedRole",
            "Resource": "*",
            "Condition": {
                "StringEquals": {"iam:AWSServiceName": "ec2.amazonaws.com"}
            },
        },
    ],
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(policy, f, indent=2)
    f.write("\n")
PY

if aws iam get-open-id-connect-provider --open-id-connect-provider-arn "${oidc_provider_arn}" >/dev/null 2>&1; then
  echo "OIDC provider already exists: ${oidc_provider_arn}"
else
  aws iam create-open-id-connect-provider \
    --url "https://token.actions.githubusercontent.com" \
    --client-id-list "sts.amazonaws.com" \
    --thumbprint-list "6938fd4d98bab03faadb97b34396831e3780aea1" >/dev/null
  echo "Created OIDC provider: ${oidc_provider_arn}"
fi

if aws iam get-role --role-name "${role_name}" >/dev/null 2>&1; then
  aws iam update-assume-role-policy \
    --role-name "${role_name}" \
    --policy-document "file://${trust_policy}" >/dev/null
  aws iam update-role \
    --role-name "${role_name}" \
    --max-session-duration 21600 >/dev/null
  echo "Updated IAM role trust policy: ${role_arn}"
else
  aws iam create-role \
    --role-name "${role_name}" \
    --assume-role-policy-document "file://${trust_policy}" \
    --max-session-duration 21600 >/dev/null
  echo "Created IAM role: ${role_arn}"
fi

aws iam put-role-policy \
  --role-name "${role_name}" \
  --policy-name "${role_name}Policy" \
  --policy-document "file://${permissions_policy}" >/dev/null
echo "Attached inline deploy policy to ${role_name}"

if [ "${generate_ssh_key}" = true ]; then
  if [ -z "${ssh_private_key_path}" ]; then
    ssh_private_key_path="${HOME}/.ssh/${ssh_key_name}.pem"
  fi
  expanded_key_path="${ssh_private_key_path/#\~/${HOME}}"
  mkdir -p "$(dirname "${expanded_key_path}")"
  if [ ! -f "${expanded_key_path}" ]; then
    ssh-keygen -t ed25519 -N "" -C "psynetskills-attempt-deploy" -f "${expanded_key_path}" >/dev/null
    chmod 600 "${expanded_key_path}"
    echo "Generated SSH private key: ${expanded_key_path}"
  else
    echo "SSH private key already exists: ${expanded_key_path}"
  fi
fi

if [ -n "${ssh_private_key_path}" ]; then
  expanded_key_path="${ssh_private_key_path/#\~/${HOME}}"
  if [ ! -f "${expanded_key_path}" ]; then
    echo "SSH private key not found: ${expanded_key_path}" >&2
    exit 1
  fi

  public_key="$(ssh-keygen -y -f "${expanded_key_path}")"
  IFS=',' read -r -a region_list <<< "${regions}"
  for region in "${region_list[@]}"; do
    region="${region//[[:space:]]/}"
    if [ -z "${region}" ]; then
      continue
    fi
    if aws ec2 describe-key-pairs --region "${region}" --key-names "${ssh_key_name}" >/dev/null 2>&1; then
      echo "EC2 key pair already exists in ${region}: ${ssh_key_name}"
    else
      aws ec2 import-key-pair \
        --region "${region}" \
        --key-name "${ssh_key_name}" \
        --public-key-material "${public_key}" >/dev/null
      echo "Imported EC2 key pair in ${region}: ${ssh_key_name}"
    fi
  done
fi

cat <<EOF

AWS setup complete.

Create the GitHub Environment '${environment_name}' without required reviewers
for no-approval deploys. Then add these Environment variables:

  ATTEMPT_DEPLOY_AWS_ROLE_ARN=${role_arn}
  ATTEMPT_DEPLOY_AWS_REGION=${regions%%,*}
  ATTEMPT_DEPLOY_SSH_KEY_NAME=${ssh_key_name}

Add these Environment secrets:

  ATTEMPT_DEPLOY_SSH_PRIVATE_KEY  # contents of the private key file
  ATTEMPT_DEPLOY_DASHBOARD_USER
  ATTEMPT_DEPLOY_DASHBOARD_PASSWORD

The role trust policy only accepts OIDC tokens with subject:

  ${oidc_subject}

In this no-reviewer mode, anyone who can dispatch the workflow can start a real
EC2 deployment. Add required reviewers later if you want a separate human gate.
EOF
