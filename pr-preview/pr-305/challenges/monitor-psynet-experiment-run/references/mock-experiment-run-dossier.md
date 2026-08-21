# Mock experiment run dossier

This dossier is fictional. It is intended for a local/mock PsyNetSkills
challenge only. Do not treat any names, URLs, identifiers, logs, paths, or
participant summaries as real deployment information.

## Run metadata

- Experiment folder: `experiments/pitch-memory-local-pilot`
- Branch: `cursor/mock-pitch-memory-monitoring`
- App name: `mock-pitch-memory-pilot-20260615`
- Server name: `mock-hotair-staging-01`
- DNS host: `mock-hotair-staging-01.example.invalid`
- Dashboard URL: `http://localhost:5000/dashboard`
- Recruiter: local/mock recruiter only
- Run state: local pilot monitoring, not production
- Recruitment state: open for local testers until four main-task completions
- Expected main-task completions: 4
- Expected prescreener checks: at least one pass and one clean failure path
- Expected main-task trials per completed participant: 8 pitch-memory trials
- Expected practice trials per completed participant: 2 practice trials
- Expected condition assignment: alternating `low-load` and `high-load`
- Export path under review:
  `exports/mock-pitch-memory-pilot-20260615/2026-06-15T05-40Z/`

## Participant-flow notes

These notes come from a mock browser walkthrough and scripted local participant
checks.

| Check | Mock evidence | Status |
| --- | --- | --- |
| Ad/consent page | `ad.html` and consent text loaded at `http://localhost:5000/ad` | Pass |
| Instructions | Main instructions and volume-check instructions displayed before trials | Pass |
| Media/assets | `tone_A4.wav`, `tone_C5.wav`, and `tone_E5.wav` loaded during representative trials | Pass |
| Representative trials | One scripted tester completed two practice trials and eight main trials | Pass |
| Prescreener pass path | Participant `P001` passed the audio-identification prescreener and entered the main task | Pass |
| Prescreener fail path | Participant `P004` failed the audio-identification prescreener and reached an unsuccessful end page before any main-task trials | Pass |
| Completion redirect | Participants `P001`, `P002`, and `P003` reached `/recruiter-exit?status=complete` | Pass |

## Mock application logs

```text
2026-06-15T05:12:04Z INFO app=mock-pitch-memory-pilot-20260615 server=mock-hotair-staging-01 boot ok
2026-06-15T05:13:18Z INFO assets loaded manifest=assets/pitch_memory_manifest.json count=3
2026-06-15T05:17:43Z INFO participant=P001 prescreener=audio_identification result=pass
2026-06-15T05:20:12Z INFO participant=P001 completed_trials main=8 practice=2 redirect=/recruiter-exit?status=complete
2026-06-15T05:23:08Z INFO participant=P002 prescreener=audio_identification result=pass
2026-06-15T05:25:33Z WARN participant=P002 focus_loss_count=1 page=trial
2026-06-15T05:28:11Z INFO participant=P002 completed_trials main=8 practice=2 redirect=/recruiter-exit?status=complete
2026-06-15T05:31:04Z INFO participant=P003 prescreener=audio_identification result=pass
2026-06-15T05:34:21Z WARN participant=P003 median_response_ms=390 quality_flag=fast_responses
2026-06-15T05:35:07Z INFO participant=P003 completed_trials main=8 practice=2 redirect=/recruiter-exit?status=complete
2026-06-15T05:36:42Z INFO participant=P004 prescreener=audio_identification result=fail failure_tags=audio_prescreener
2026-06-15T05:36:43Z INFO participant=P004 unsuccessful_end no_main_trials=true
2026-06-15T05:39:19Z INFO participant=P005 started page=instructions assigned_condition=high-load
2026-06-15T05:40:19Z WARN participant=P005 idle_seconds=60 page=instructions
2026-06-15T05:41:19Z WARN participant=P005 idle_seconds=120 page=instructions
2026-06-15T05:42:19Z INFO export path=exports/mock-pitch-memory-pilot-20260615/2026-06-15T05-40Z status=partial
```

No log line shows a repeated server error, missing required audio asset, failed
database write, failed redirect for a completed participant, paid-recruitment
event, app destruction, or EC2 teardown.

## Export summary

The current export is an interim local export for monitoring. It is not a final
handoff export because the stopping rule has not been met.

### Participants

| participant_id | status | condition | prescreener | main_trials | practice_trials | redirect | quality_flags |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| P001 | complete | low-load | pass | 8 | 2 | `/recruiter-exit?status=complete` | none |
| P002 | complete | high-load | pass | 8 | 2 | `/recruiter-exit?status=complete` | focus_loss_count=1 |
| P003 | complete | low-load | pass | 8 | 2 | `/recruiter-exit?status=complete` | fast_responses |
| P004 | failed | not-assigned | fail | 0 | 0 | unsuccessful end page | audio_prescreener |
| P005 | active | high-load | not-started | 0 | 0 | none yet | idle_at_instructions |

### Trial rows

- Main-task trial rows exported: 24
- Expected from completed participants: 3 completed participants x 8 main trials
  = 24
- Practice trial rows exported: 6
- Failed prescreener participant `P004` has 0 main-task and 0 practice trial rows
- Active participant `P005` has no trial rows yet

### Module states and metadata

- Consent/ad state recorded for participants `P001` through `P005`
- Instruction state recorded for participants `P001` through `P005`
- Audio prescreener state recorded for `P001` through `P004`
- Completion state recorded for `P001`, `P002`, and `P003`
- Unsuccessful-end state recorded for `P004` with `failure_tags=["audio_prescreener"]`
- No completion state yet for `P005`
- Required metadata fields present: `participant_id`, `status`,
  `assigned_condition`, `trial_index`, `stimulus_id`, `response`, `response_ms`,
  `quality_flags`, `module_state`, `started_at`, and `completed_at`

## Ambiguous issues to assess conservatively

1. Participant `P003` completed the required trials and redirect, but has a
   `fast_responses` quality flag. This is review-worthy telemetry, not proof of
   bot use, AI use, bad faith, or unusable data.
2. Participant `P005` is assigned to `high-load` and appears idle on the
   instructions page. The participant has not consumed main-task trials, but the
   run has only three of four expected main-task completions.
3. The interim export is internally coherent for completed and failed
   participants, but it is explicitly marked `status=partial`.
