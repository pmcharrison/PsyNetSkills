# Plan

## Methods

This experiment will collect subjective liking ratings for music excerpts. Each participant will first see a welcome page and task instructions, then complete an audio-hearing prescreen, and only participants who pass the prescreen will proceed to the main rating task. The main task will consist of 30 trials per participant by default. On each trial, the participant will listen to one MP3 excerpt and provide a single rating on a discrete 1-9 scale, where 1 is labeled as strong dislike and 9 as strong liking. The experiment will end with a brief completion page.

The materials will be defined by `static/songs.csv`, which must contain `track_id` and `s3_url`. The current challenge snapshot contains 30 tracks with S3-hosted MP3 URLs, so the default run can present each track once per participant. Trial order will be randomized per participant while preserving the one-rating-per-track structure. If a future demonstration CSV contains fewer than 30 rows, the implementation will sample with replacement to reach 30 trials and document that policy in the report.

The prescreen will use a short audio forced-choice task before the main rating trials. The prescreen stimuli will be generated or bundled locally as simple MP3 clips at a volume chosen to be comparable to the music excerpts. Participants will hear the clips and answer a simple question with a known correct answer, such as identifying which of several words, tones, or short cues was played. The task will require enough correct responses to show that the participant can hear audio before they begin rating songs.

Saved data will support reconstruction of the participant flow. Each rating record will include the participant/session identifier, trial index, `track_id`, `s3_url`, the 1-9 rating, and a flag or participant variable indicating that the audio prescreen was passed. Prescreen trial data will also be saved by PsyNet so reviewers can inspect pass/fail behavior separately from main ratings.

## Implementation

The experiment code will live under `code/song_rating_experiment/` to avoid naming collisions with Python's standard-library `code` module. It will be a self-contained PsyNet experiment with the usual support files needed for local launch checks.

Implementation will follow the PsyNet `simple_audio_rating` demo pattern. A CSV loader will read `static/songs.csv`, validate that the required columns exist, validate that at least 30 rows are present for the default design, and construct one `StaticNode` per row. Each node definition will include `track_id` and `s3_url`. The remote MP3 will be represented with PsyNet's `ExternalAsset` rather than being downloaded or re-uploaded. The trial class will subclass `StaticTrial` and show a `ModularPage` with an `AudioPrompt` and a single `RatingScale`/rating control constrained to 1-9. Submission will be enabled after the prompt has played enough to demonstrate that the audio path works, following the `promptEnd` event pattern from the audio rating demo where appropriate.

The audio prescreen will use PsyNet's `AudioForcedChoiceTest` if compatible with generated local assets. A small `static/prescreen.csv` will describe the prescreen clips, correct answers, and prompts. If `AudioForcedChoiceTest` requires URL-style assets that are awkward for local generated clips, the fallback will be a minimal `StaticTrialMaker` using the same `AudioPrompt` plus `PushButtonControl` scoring pattern from `AudioForcedChoiceTrial`. In either case, the prescreen will appear before the rating trial maker in the `Timeline`, will enforce a performance threshold, and will prevent failed participants from continuing to the rating trials.

The experiment class will set local-test parameters for enough bots to exercise the prescreen and the 30-trial path. Bot behavior will answer the prescreen correctly and provide deterministic or seeded pseudo-random 1-9 ratings so `psynet test local`, `psynet simulate`, and the analysis notebook exercise the same data path as real participants. The implementation will avoid production credentials and will use the public S3 URLs already present in `static/songs.csv`.

Planned validation and evidence after approval:

1. Run `python experiment.py` from `code/song_rating_experiment/` to validate and list the 30 stimuli.
2. Run `psynet test local` to exercise the participant timeline with bots.
3. Run `psynet debug local` and collect participant-facing evidence with the `record-participant-video` workflow, including the audio prescreen and at least one song rating trial.
4. Run `psynet simulate` and save `evidence/simulated_data.zip`.
5. Run the performance test described by the validation guidance and save `evidence/performance.json`, or record a blocker if local services prevent it.
6. Export or save review logs and a monitor snapshot under `evidence/`.
7. Create and execute `evidence/analyses/analysis.ipynb`, keeping it under the dashboard size limit, with visible CSV-reading code, summary tables, and a simple plot or table of simulated ratings by track.
8. Write `REPORT.md` summarizing implementation, validation, simulation, analysis, limitations, and any evidence blockers.
