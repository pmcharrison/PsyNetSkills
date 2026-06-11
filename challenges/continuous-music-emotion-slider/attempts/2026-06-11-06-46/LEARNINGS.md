# Learnings

## PsyNet local export password fallback

`psynet export local --username ... --password ...` still attempted to read `dashboard_password` from config in this environment. Directly downloading `/dashboard/export/download?type=psynet&anonymize=no&assets=none` with the local dashboard credentials produced the expected export ZIP.

*Actions:*
- **PsyNet:** Check whether `psynet export local` should honor explicit `--username`/`--password` before reading dashboard credentials from config. Confidence: medium. Status: considering.

## Participant recording path discipline

The first ffmpeg recording command used `evidence/participant.mp4` from inside the experiment directory, where no `evidence/` folder exists. Using the attempt-relative path `../../evidence/participant.mp4` fixed the issue.

*Actions:*
- **PsyNetSkills:** Consider adding an explicit reminder in participant-video guidance to run ffmpeg from the experiment directory with an attempt-relative evidence path. Confidence: medium. Status: considering.

## Evidence should prove active multi-slider movement

The first participant recordings showed both dimensions on screen but only one slider visibly changing during playback. Video review caught this gap. Locking sliders after `promptEnd`, using longer local demo clips, and scripting a visible participant pass produced clearer evidence without changing the stored trajectory schema.

*Actions:*
- **PsyNetSkills:** Consider asking challenge agents to review videos specifically for active interaction with every required response dimension, not only for control presence. Confidence: high. Status: considering.

## Simulated trajectories should encode expected patterns

The evaluator noted that the attempt validates the workflow well, but future versions would be more informative with richer stimulus metadata and more realistic trajectory-generating profiles. That would let the analysis test expected stimulus/condition patterns instead of mostly checking that the pipeline runs.

*Actions:*
- **PsyNetSkills:** Consider encouraging emotion-trajectory challenge attempts to include condition-specific simulated response profiles and richer stimulus metadata when real participant data are unavailable. Confidence: high. Status: considering.
