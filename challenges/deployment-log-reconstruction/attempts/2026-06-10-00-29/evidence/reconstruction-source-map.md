# Reconstruction source map

## Recorded facts used

- Folder notes identify `/experiments/global-rhythm-validation`, Dockertag
  `global-rhythm-validation`, recruiter Prolific, and intended app name
  `ww-global-rhythm-val`.
- Terminal history records the EC2 provision command with server name
  `ww-global-rhythm-val`, region `us-east-2`, DNS host
  `ww-global-rhythm-val.cap-experiments.com`, and instance type `m7i.xlarge`.
- Terminal history records the SSH deploy command with app
  `ww-global-rhythm-val`, DNS host `ww-global-rhythm-val.cap-experiments.com`,
  and server `ww-global-rhythm-val.cap-experiments.com`.
- Deploy output reports experiment UID `abc123-demo-uid`, 24 uploaded WAV assets,
  dashboard URL
  `https://ww-global-rhythm-val.ww-global-rhythm-val.cap-experiments.com/dashboard`,
  logs URL `https://logs.ww-global-rhythm-val.cap-experiments.com`, and status
  `Success`.
- Follow-up notes report one transient TLS/SSL error on first launch and a
  successful second launch two minutes later without code changes.
- Export listing shows `Participant.csv`, `Response.csv`, `Trial.csv`, and
  `source_code.zip` under
  `/experiments/global-rhythm-validation/exports/ww-global-rhythm-val-2026-06-07/`.
- Cleanup notes report no recorded destroy or teardown commands and unknown
  current server state.

## Inferences and uncertainty handling

- Server name is marked as candidate because `--name ww-global-rhythm-val`
  appears in the provision command, while deploy uses the fully qualified host in
  `--server`.
- Export command is marked as candidate because only an export folder listing is
  present.
- Export status is marked partial/unknown because the listed files do not prove
  data completeness, asset archival, row counts, payment data, or checksums.
- Destroy and teardown commands are marked candidate and unsafe to run without
  human approval because cleanup was not recorded and export completeness is not
  confirmed.
- The dashboard URL is copied exactly as reported and flagged for confirmation
  because it includes both the app name and server host.
