# Report

## Summary

This attempt implements a runnable PsyNet song-rating experiment. Participants
complete a short audio-hearing prescreen, then rate 30 S3-hosted song excerpts
on a 1-9 liking scale. The implementation is self-contained in
`code/song_rating_experiment/`.

## Implementation

The experiment reads `static/songs.csv` with `track_id` and `s3_url` columns and
constructs one PsyNet `StaticNode` per song. Song audio is represented as
`ExternalAsset` instances so the browser plays the real public S3 MP3 links.
The main rating trial uses `AudioPrompt` plus `RatingControl`; song playback is
limited to the first 10 seconds with `play_window=[0, 10]` so the default
30-trial session is practical.

The prescreen uses three generated WAV tone cues at a moderate amplitude,
presented through a static trial maker before the song ratings. Participants
must answer at least two of three forced-choice tone trials correctly to proceed.
The prescreen tones are generated at a level intended to be comparable to the
song excerpts, subject to browser and device playback settings.

## Validation

Functional bot validation passed with `psynet test local`. The experiment's bot
checks assert that each bot completes three prescreen trials, passes the
prescreen, and records exactly 30 song-rating trials with track IDs, S3 URLs,
and ratings in the 1-9 range.

The final simulation export contains 3 approved bot participants, 9 audio
prescreen trials, and 90 song-rating trials. The canonical notebook at
`evidence/analyses/analysis.ipynb` reads the exported CSV data directly and
summarizes participant, prescreen, and per-track rating data.

The final performance test ran for 5 minutes with 40 concurrent bots. It
reported 0 bot errors, 0 request errors, 2,759 total requests, median response
time 0.108 seconds, and 95th percentile response time 1.042 seconds.

## Participant-facing evidence

`evidence/participant.mp4` shows the participant-facing flow from consent through
welcome, volume instructions, audio prescreen, first song-rating trial, scripted
completion of the remaining ratings, and the final completion page. The video is
silent because it is derived from Playwright's browser recording, but visual
behavior and audio-gated response enabling are covered by the Playwright test and
screenshots in `evidence/screenshots/`.

A manual browser check with the computer-use agent independently verified the
ad, consent, welcome, and prescreen UI. It did not reach the song-rating phase
because the agent cannot reliably hear and answer the forced-choice tones; the
scripted Playwright evidence completed that path using the known test audio
mapping.

## Limitations

The simulated ratings are deterministic bot responses and should be interpreted
only as workflow validation, not as human preference data. The prescreen volume
is generated at a moderate digital amplitude, but exact loudness comparability
depends on browser playback and participant device settings.
