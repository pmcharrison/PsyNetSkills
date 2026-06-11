# Methods and results report

## Methods

This attempt implements a brief local PsyNet demonstration asking whether short surprising facts elicit higher curiosity ratings than ordinary facts. The task presents six hand-authored text stimuli: three internally labelled `surprising` and three internally labelled `ordinary`. On each static PsyNet trial, the participant reads one fact and rates curiosity on a 1-7 numeric radio-button scale, where 1 means "not curious at all" and 7 means "extremely curious".

The experiment uses local PsyNet bot participants only. Bot responses are deterministic pseudo-behaviour for an end-to-end data demonstration: surprising facts receive ratings of 6 or 7 and ordinary facts receive ratings of 3 or 4. These bot responses are not evidence about human psychology.

## Export and analysis plan

After running the experiment locally, exported PsyNet data will be saved under `evidence/data_export/` and compressed to `evidence/data.zip`. The analysis script in `code/curiosity_discovery/analysis.py` reads the exported basic-data `trial.csv` and `participant.csv` files, then reports participant count, trial count, and curiosity ratings summarized by stimulus condition.

## Results

Results will be filled in after local bot execution, data export, and analysis.
