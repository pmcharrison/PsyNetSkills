# Continuous music emotion slider

This is a local-only PsyNet experiment for collecting time-resolved perceived-emotion ratings from short audio clips. It uses three committed/generated WAV files in `static/stimuli/` and never uses recruitment services, production credentials, private audio, AWS, Prolific, Cint, or copyrighted downloads.

## Participant task

Each trial plays a short generated clip automatically. Participants continuously rate the perceived emotion in the sound, not their own mood, on two dimensions:

- valence: negative to positive
- arousal: calm to energetic

The custom control stores repeated timestamped samples for both dimensions during playback. Sampling policy: the browser samples both sliders every 250 ms from `promptStart` until `promptEnd`, and also adds an immediate sample whenever either slider moves. The Next button is enabled only after `promptEnd`, so participants cannot finish before the rating window is complete.

## Stimulus replacement

Replace `stimulus_metadata.csv` and the files referenced by `audio_path` with study-owned clips. Required metadata columns are:

- `stimulus_id`: stable unique identifier used in trial answers and analysis
- `audio_path`: local path to a committed or deployed audio asset
- `condition`: analysis grouping, such as experimental condition
- `excerpt_type`: short description of excerpt/source class
- `intended_affect`: optional planned affective category for balancing/analysis
- `duration_seconds`: rating-window duration, normally matching clip length

## Local commands

```bash
cd challenges/continuous-music-emotion-slider/attempts/2026-06-11-06-46/code/continuous_music_emotion_slider
source ~/PsyNet/.venv/bin/activate
psynet test local
python analyze.py --simulate-if-missing
```

The analysis command reads PsyNet-shaped JSONL trial records from `../../evidence/simulated_psynet_trials.jsonl`, creating deterministic simulated bot data when that file is absent, and writes long-format samples plus summaries into `../../evidence/analysis/`.

Bot/simulated outputs validate the data flow only and should not be interpreted as real emotion data.
