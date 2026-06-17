---
title: Song rating experiment
type: experiment implementation
difficulty: 4
authors: [lucasgautheron]
---

Implement a PsyNet experiment where participants listen to short music excerpts
and rate each excerpt on a discrete scale from 1 to 9.

The experiment should run locally in a standard PsyNet development environment.
Do not use real participant recruitment, production credentials, private storage
credentials, or URLs that require authentication. The song metadata should come
from a CSV file at `static/songs.csv`.

## Participant experience

Participants should first complete a short welcome and instruction sequence that
explains the rating task. The main task should then present a series of music
rating trials. On each trial:

1. The participant is shown simple instructions for the current song.
2. The participant hears one song excerpt loaded from the `s3_url` field in the
   song metadata.
3. The participant rates the song on a 1 to 9 scale.
4. The trial saves exactly one rating before moving on to the next song.

Use clear scale labels so participants understand the rating direction. For
example, 1 may mean "do not like it at all" and 9 may mean "like it very much".

## Stimuli and trial structure

The stimulus list must be read from `static/songs.csv`, which contains exactly
these required columns:

- `track_id`: a stable song or excerpt identifier;
- `s3_url`: an HTTP or HTTPS URL pointing directly to an MP3 file.

The attempt may use a PsyNet static trial maker. Require 30 rating trials per
participant by default. If the demonstration CSV contains fewer than 30 songs,
document the sampling policy used to reach 30 trials, such as cycling through
the list or sampling with replacement. The implementation should make it easy
for a researcher to replace the demonstration CSV with a larger `static/songs.csv`
file without changing the experiment logic.

## Audio prescreening

Before the rating trials, include an audio-hearing prescreen. The prescreen
should verify that participants can hear audio clearly enough to complete the
music rating task. Where possible, use audio presented at a level comparable to
the song excerpts, not a much louder or quieter cue. Participants who fail the
prescreen should not proceed to the main rating trials.

## Data requirements

Save enough structured data to reconstruct every rating trial. At minimum, each
saved rating should include:

- the participant or bot session;
- the trial index;
- the `track_id`;
- the `s3_url` used for playback;
- the 1 to 9 rating value;
- whether the participant passed the audio prescreen.

## Validation and evidence

The attempt should include local run instructions and demonstrate that the
experiment runs with PsyNet bots or a local participant flow. Provide
participant-facing evidence, such as a browser video or screenshots, showing the
audio prescreen and at least one music rating trial. If the evidence uses
placeholder URLs or simulated audio, state that clearly and explain how to
replace `static/songs.csv` with real study stimuli.
