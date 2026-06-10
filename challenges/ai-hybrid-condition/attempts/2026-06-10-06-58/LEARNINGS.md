# Learnings

## Local export credential inference

`psynet export local --username ... --password ...` still attempted to read
`dashboard_password` from config during this debug launch, so the export was
collected from the same dashboard endpoint that the CLI calls internally.

*Actions:*
- **PsyNet:** Check whether `psynet export local` should honor explicit `--username` and `--password` before reading dashboard credentials from config. Confidence: medium. Status: considering.
