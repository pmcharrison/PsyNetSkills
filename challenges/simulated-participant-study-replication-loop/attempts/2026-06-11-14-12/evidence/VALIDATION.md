# Validation evidence

## Commands run

- `python3 simulate_profiles.py --run-id initial --seed 577 --output-dir ../../evidence/exports/initial_data`
  - Wrote `evidence/exports/initial_data.zip`.
- `python3 simulate_profiles.py --run-id revised --seed 578 --revised --output-dir ../../evidence/exports/revised_data`
  - Wrote `evidence/exports/revised_data.zip`.
- `python3 analyze_exports.py --initial-zip ../../evidence/exports/initial_data.zip --revised-zip ../../evidence/exports/revised_data.zip --output-dir ../../evidence/analysis`
  - Wrote initial, revised, and comparison analysis outputs.
- `dallinger constraints generate`
  - Generated `code/replication_memory/constraints.txt` from the pinned PsyNet requirement.
- `psynet test local`
  - Passed: 3 tests, including the launched PsyNet experiment and framework bots.
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output ../../evidence/performance.json`
  - Passed with 0 bot errors, 3271 requests, 10.73 requests/s, and 1.331s P95 response time.
- `ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height,avg_frame_rate -of json evidence/participant.mp4`
  - Confirmed `participant.mp4` is H.264, 1280x720, 15 fps, 13.6 seconds, 402841 bytes.

## Manual/visual evidence

- `participant.mp4` shows the participant ad page, a representative memory trial response sequence, and the 100% completion page.
- `screenshots/instructions.webp` preserves the instruction page.
- `screenshots/trial_example.webp` preserves a representative trial.
- `screenshots/completion.webp` preserves the completion page from the manual browser run.
- `monitor.html` is a local PsyNet dashboard snapshot from the debug run.

## Notes

The experiment has no audio stimuli, so `participant.mp4` is screen-only. The
full eight-trial structure is covered by `psynet test local`, the 40-bot
performance test, and the committed initial/revised simulation exports.
