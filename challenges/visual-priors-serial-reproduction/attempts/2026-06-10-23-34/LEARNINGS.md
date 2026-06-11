# Learnings

## Local export credential path

`psynet export local` with the default dashboard-download path still read
`dashboard_password` from local config even when `--username` and `--password`
were provided. The legacy local exporter avoided this for the challenge evidence
run.

*Actions:*
- **PsyNet:** Make `psynet export local --username/--password` feed the dashboard request, or document that those options do not apply before the config lookup. Confidence: medium. Status: considering.

## Use absolute evidence paths for PsyNet exports

The legacy exporter failed when given a relative path from the nested experiment
directory because a subprocess resolved it from a different working directory.
Using an absolute path under the attempt evidence directory made the export
repeatable.

*Actions:*
- **PsyNetSkills:** Recommend absolute paths for `psynet export local --path` in challenge evidence instructions. Confidence: high. Status: considering.
