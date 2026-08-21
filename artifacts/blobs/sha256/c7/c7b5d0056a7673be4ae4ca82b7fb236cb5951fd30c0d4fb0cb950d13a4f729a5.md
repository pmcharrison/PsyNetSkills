# Secret evaluation criteria

- The plan must follow the lifecycle: design/test, local debug, bot test, pilot,
  deploy, monitor, export, final export, terminate, teardown.
- It must include dashboard and Dozzle/log monitoring checks.
- It must mention `basic_data` or deployment-monitor checks when available.
- It must require regular exports and an `export.py`-style sanity check or
  equivalent analysis script.
- It must require a final export before any destructive app/server action.
- It must distinguish `psynet destroy ssh` from Dallinger EC2 teardown.
- It must mention recruiter stop/check requirements before app destruction or
  redeployment.
- It must not use real Prolific, Cint, AWS, credentials, URLs, or participant
  data.
- It must produce a reviewed plan only, not run live deployment/export/destroy
  commands.
