# Learnings

## Local export credentials may need environment variables

`psynet export local` did not pick up the local debug dashboard password from
CLI flags in this Cursor Cloud run, but succeeded when `dashboard_user` and
`dashboard_password` were supplied as environment variables for the export
process.

*Actions:*
- **PsyNetSkills:** Update experiment-evidence or validation guidance to mention using local ephemeral `dashboard_user` and `dashboard_password` environment variables when `psynet export local` cannot infer debug dashboard credentials. Confidence: medium. Impact: low. Status: considering.
