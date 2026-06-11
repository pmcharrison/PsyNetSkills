# Methods and results report

## Methods

This attempt implements a brief local PsyNet demonstration asking whether short surprising facts elicit higher curiosity ratings than ordinary facts. The task presents six hand-authored text stimuli: three internally labelled `surprising` and three internally labelled `ordinary`. On each static PsyNet trial, the participant reads one fact and rates curiosity on a 1-7 numeric radio-button scale, where 1 means "not curious at all" and 7 means "extremely curious".

The canonical local data run used PsyNet simulated bot participants through `psynet simulate`, which runs the experiment's local regression test and then exports the local PsyNet data. Bot responses are deterministic pseudo-behaviour for an end-to-end data demonstration: surprising facts receive ratings of 6 or 7 and ordinary facts receive ratings of 3 or 4. These bot responses are not evidence about human psychology and should not be interpreted as human curiosity data.

Participant-facing behavior was separately checked in a browser recording (`evidence/participant.mp4`) by completing one local participant flow from the ad page through the final completion page.

## Export and analysis

The local PsyNet export was written by `psynet simulate` to `data/simulated_data`, copied into the attempt evidence as `evidence/data.zip`, and analyzed by `code/curiosity_discovery/analysis.py`. The script reads the exported basic-data `trial.csv` and `participant.csv` files and writes `evidence/analysis_results.json`.

## Results

The exported simulated dataset contained 3 bot participants and 18 curiosity-rating trials. Each participant completed all six stimuli, producing 9 ordinary-condition trials and 9 surprising-condition trials.

Descriptive statistics from `evidence/analysis_results.json`:

| Condition | Trials | Mean curiosity rating | Min | Max |
| --- | ---: | ---: | ---: | ---: |
| ordinary | 9 | 3.667 | 3.0 | 4.0 |
| surprising | 9 | 6.667 | 6.0 | 7.0 |

These values reflect the deterministic simulated bot response rule, not a psychological finding about people.
