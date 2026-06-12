# Learnings

## Stop debug server before performance testing

`psynet performance-test local` starts its own server on port 5000. Running it while `psynet debug local` was still alive caused a port-conflict startup failure before any bots could run.

*Actions:*

- **PsyNetSkills:** Update experiment evidence guidance to remind agents to stop or avoid a live `psynet debug local` server on port 5000 before running `psynet performance-test local`, because the performance test starts its own local server. Confidence: high. Impact: medium. Status: considering.

## Use legacy local export after server shutdown

After the performance server had stopped, `psynet export local` could not infer a dashboard password, while `psynet export local --legacy --path <absolute evidence path> --assets none --no-source` successfully exported the local database.

*Actions:*

- **PsyNetSkills:** Update experiment evidence guidance to recommend `psynet export local --legacy --path <absolute evidence path> --assets none --no-source` when exporting local data after a debug or performance server has stopped or dashboard credentials are unavailable. Confidence: medium. Impact: medium. Status: considering.
