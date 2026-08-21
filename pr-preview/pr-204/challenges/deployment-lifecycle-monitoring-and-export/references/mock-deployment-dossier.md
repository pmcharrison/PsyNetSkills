# Mock deployment dossier

This dossier is fictional. It contains no real credentials, URLs, recruiter
accounts, cloud resources, participant data, or deployment records.

## Study summary

- Study nickname: Mock Echo Span Pilot
- Experiment folder: `experiments/mock_echo_span`
- App name: `mock-echo-span-pilot-app`
- Server name: `mock-psynet-lab-server-07`
- Recruiter: `mock-recruiter-sandbox`
- Target pilot sample: 8 mock participants
- Target full sample: 120 mock participants
- Current lifecycle state: pilot completed, full launch not yet approved

## Mock links

- Dashboard URL: `https://dashboard.mock.example.invalid/apps/mock-echo-span-pilot-app`
- Dozzle URL: `https://logs.mock.example.invalid/container/mock-echo-span-pilot-app`
- Deployment monitor URL: `https://monitor.mock.example.invalid/deployments/mock-echo-span-pilot-app`
- Export folder: `mock_exports/mock_echo_span/`

## Local and bot testing notes

- Local debug: completed once with no blocking errors recorded.
- Bot test: completed with 12 mock bot sessions.
- Known warning: one mock bot timed out during the consent page refresh test.
- Required before live deployment: repeat local debug and bot testing after any
  experiment code or configuration change.

## Pilot status

- Pilot recruitment status: mock recruiter paused after pilot target reached.
- Dashboard state: app responding; no active mock participants currently in
  progress.
- Dozzle/log state: last reviewed logs showed no repeated worker crashes.
- `basic_data` availability: mock table available from the most recent export.
- Deployment-monitor availability: mock monitor report available for app uptime
  and recent error count.

## Mock export status

- Last regular export: `mock_exports/mock_echo_span/export_2026-06-01T120000Z.zip`
- Last export sanity check: passed expected mock trial count and completion-rate
  checks.
- Final export: not yet completed.
- Open issue: final export must be completed and checked before any app
  destruction, redeployment, or server teardown.

## Teardown notes

- App destruction candidate: `mock-echo-span-pilot-app`
- Server teardown candidate: `mock-psynet-lab-server-07`
- Human review required before destructive actions: yes
- Recruiter stop/check required before app destruction or redeployment: yes
- Reminder: app destruction and EC2 server teardown are separate lifecycle
  actions and should not be treated as interchangeable.
