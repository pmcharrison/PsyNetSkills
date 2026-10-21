# Messy Deployment Dossier

Use this dossier to reconstruct a clean `DEPLOYMENT_LOG.md`.

## Folder Notes

- Local folder: `/experiments/global-rhythm-validation`
- `Dockertag`: `global-rhythm-validation`
- Recruiter: Prolific
- Intended app name appears to be `ww-global-rhythm-val`

## Partial Terminal History

```bash
dallinger ec2 provision --name ww-global-rhythm-val --region us-east-2 --dns-host ww-global-rhythm-val.cap-experiments.com --type m7i.xlarge
psynet deploy ssh --app ww-global-rhythm-val --dns-host ww-global-rhythm-val.cap-experiments.com --server ww-global-rhythm-val.cap-experiments.com
```

Deploy output mentioned:

- Experiment UID: `abc123-demo-uid`
- Assets uploaded: 24 WAVs
- Dashboard: `https://ww-global-rhythm-val.ww-global-rhythm-val.cap-experiments.com/dashboard`
- Logs: `https://logs.ww-global-rhythm-val.cap-experiments.com`
- Status: Success

## Follow-up Notes

First launch produced a transient TLS/SSL error. A second launch two minutes
later worked without code changes.

## Export Folder Listing

```text
exports/
  ww-global-rhythm-val-2026-06-07/
    Participant.csv
    Response.csv
    Trial.csv
    source_code.zip
```

## Cleanup Notes

No destroy or teardown commands are recorded. It is unknown whether the server
is still running.

