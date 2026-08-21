# Deployment Log

## Summary

- Experiment folder path: `/experiments/global-rhythm-validation`
- Dockertag: `global-rhythm-validation`
- Deployment status: recorded deploy output says `Success` after a transient first-launch TLS/SSL error.
- Server state: `TODO` - cleanup notes do not confirm whether the server is still running.

## Deployment identifiers

| Field | Value | Confidence / notes |
| --- | --- | --- |
| App name | `ww-global-rhythm-val` | Recorded as the intended app name and used in the deploy command. |
| Candidate server name | `ww-global-rhythm-val` | Inferred from `dallinger ec2 provision --name`; confirm before teardown. |
| Server host | `ww-global-rhythm-val.cap-experiments.com` | Used as both `--dns-host` and `--server`. |
| DNS host | `ww-global-rhythm-val.cap-experiments.com` | Recorded in provision and deploy commands. |
| AWS region | `us-east-2` | Recorded in the provision command. |
| Instance type | `m7i.xlarge` | Recorded in the provision command. |
| Experiment UID | `abc123-demo-uid` | Reported by deploy output. |
| Recruiter | Prolific | Recorded in folder notes. |
| Qualification/config files | `TODO` | No qualification or config filenames were present in the dossier. |

## Provisioning

Recorded provision command:

```bash
dallinger ec2 provision --name ww-global-rhythm-val --region us-east-2 --dns-host ww-global-rhythm-val.cap-experiments.com --type m7i.xlarge
```

## Deployment

Recorded deploy command:

```bash
psynet deploy ssh --app ww-global-rhythm-val --dns-host ww-global-rhythm-val.cap-experiments.com --server ww-global-rhythm-val.cap-experiments.com
```

Recorded deploy output:

- Assets uploaded: 24 WAVs
- Dashboard URL: `https://ww-global-rhythm-val.ww-global-rhythm-val.cap-experiments.com/dashboard`
- Logs URL: `https://logs.ww-global-rhythm-val.cap-experiments.com`
- Status: Success

The dashboard URL is copied as recorded. It contains both the app name and the
server host; confirm whether that is the intended dashboard URL or an output
artifact before sharing it with participants or operators.

## Exports

Recorded export folder:

```text
/experiments/global-rhythm-validation/exports/ww-global-rhythm-val-2026-06-07/
  Participant.csv
  Response.csv
  Trial.csv
  source_code.zip
```

Candidate export command, inferred from the app/server names and export path:

```bash
psynet export ssh --app ww-global-rhythm-val --server ww-global-rhythm-val.cap-experiments.com --path /experiments/global-rhythm-validation/exports
```

Export status: partial/unknown. The listing includes core tabular CSVs and a
source archive, but the dossier does not include an export command, checksums,
row counts, payment/recruitment exports, logs, or the 24 uploaded WAV assets.
Treat the export as insufficient for teardown until a human confirms the data
requirements.

## Destroy and teardown commands

Do not run these commands without explicit human approval and a confirmed export.

Candidate PsyNet app destroy command:

```bash
psynet destroy ssh --app ww-global-rhythm-val --server ww-global-rhythm-val.cap-experiments.com
```

Candidate EC2 teardown command:

```bash
dallinger ec2 teardown --name ww-global-rhythm-val --region us-east-2 --dns-host ww-global-rhythm-val.cap-experiments.com
```

## Unresolved questions

- Is `ww-global-rhythm-val` definitely both the app name and the EC2 server name?
- Is the recorded dashboard URL with the duplicated host prefix valid, or should
  the dashboard be hosted at `https://ww-global-rhythm-val.cap-experiments.com/dashboard`?
- Which Prolific recruiter, qualification, and config files were used?
- What exact export command was run, and from which working directory?
- Are the listed export files complete enough for the study's data retention and
  payment requirements?
- Were the 24 uploaded WAV assets exported or otherwise archived?
- Is the `ww-global-rhythm-val` server still running?
- Were any destroy or EC2 teardown commands executed after the notes were written?
- Did the transient TLS/SSL first-launch error have any participant-facing impact?
