# Learnings

## Attempt setup assumptions

This environment did not have `rsync`, while the attempt workflow benefits from a
copy command that excludes prior attempts without inspecting them.

*Actions:*
- **PsyNetSkills:** Add a portable snapshot command example to the attempt-challenge skill for systems without `rsync`. Confidence: medium. Status: considering.

## Local export credential path

`psynet export local --username ... --password ...` still attempted to read
`dashboard_password` from config in this environment. Downloading the export ZIP
from the authenticated local dashboard route worked while the debug server was
running.

*Actions:*
- **PsyNetSkills:** Document the dashboard download-route fallback for local `data.zip` evidence when `psynet export local` cannot read live credentials. Confidence: medium. Status: superseded. Notes: Superseded by the upstream fix in https://gitlab.com/PsyNetDev/PsyNet/-/merge_requests/1081; the dashboard download fallback is no longer needed for this failure mode.
- **PsyNet:** Check whether `psynet export local` should honor its CLI password option before reading `dashboard_password` from config. Confidence: medium. Status: completed. Notes: Fixed upstream in https://gitlab.com/PsyNetDev/PsyNet/-/merge_requests/1081.
