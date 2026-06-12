# Plan

## Methods

The experiment will measure explicit visual similarity judgments for simple colored circles. The stimulus set will be a small, deterministic manifest of fixed-size circles that vary only in color at first, with the stimulus representation stored as structured records so that additional dimensions such as radius can be added without changing the trial machinery. Candidate initial colors will cover clearly separated hues (for example red, orange, yellow, green, blue, and purple) while keeping circle size constant.

Each trial will begin with a fixation cross, followed by two circles displayed simultaneously to the left and right of center. Participants will rate the pair's perceived similarity on a 5-point scale, where 1 means "Completely dissimilar" and 5 means "Completely similar". All ordered stimulus pairs needed by the study will be generated as static nodes from the manifest; each participant will receive 10 randomly selected trials from that full node set. Trial records will include both stimulus definitions, pair identifiers, rating response, and reaction time.

The participant workflow will include a short instruction page, the 10 similarity trials, and a closing page. No extra visual elements beyond the instructions, fixation, two circles, rating question, and response buttons will be displayed during the task.

## Implementation

The runnable experiment will live in `code/simple_visual_similarity/` to avoid importing a package named `code`. I will copy a minimal PsyNet experiment scaffold, including standard support files such as `.gitignore`, `config.txt`, `requirements.txt`, `constraints.txt`, `Dockerfile`, `Dockertag`, `pytest.ini`, and `test.py` where appropriate. `requirements.txt` will pin PsyNet to the refreshed local checkout commit recorded in `agent.json`; `constraints.txt` will be regenerated after implementation.

The core experiment will use `StaticNode`, `StaticTrial`, and `StaticTrialMaker`, following the PsyNet pair-rating pattern in `~/PsyNet/demos/pipelines/similarity/experiment.py`. Stimuli will be represented by a committed manifest-generating module or JSON file, with fields such as `stimulus_id`, `color`, `radius`, and display metadata. Pair generation will be deterministic and will include all stimulus pairs; I will decide during implementation whether identical pairs are included by default, because the public instructions say "all stimulus pairs" and the analysis heatmap is most useful with diagonal self-pairs.

The trial page will use `ModularPage` with `GraphicPrompt`, `Frame`, `Text`, and `Circle` from PsyNet Graphics. The first frame will show only the fixation cross for a short fixed duration. The second frame will show the two circles and activate response/submission via `activate_control_response` and `activate_control_submit`, so response timing starts after stimulus onset rather than during fixation. The response control will use `KeyboardPushButtonControl` with choices `1` through `5`, matching numeric keyboard keys and horizontal push buttons. Bot responses will choose valid ratings so `psynet test local`, simulation, and performance checks exercise the full path.

Reaction time will be derived from PsyNet's response/event data wherever possible, using the native control and event timeline. If the formatted answer does not already expose the needed timing, I will add a minimal, isolated trial-level extraction method or metadata field that computes time from stimulus-response events rather than adding broad custom JavaScript.

I will add `test_experiment` or `test_check_bot` assertions to verify that one bot completes exactly 10 trials, all saved trials have valid pair definitions, ratings are in the 1-5 range, and reaction-time information is present. I will also include an analysis notebook or script under the experiment directory, likely `analysis.ipynb` or `analysis.py`, that loads exported or simulated data and writes a similarity-rating heatmap plus a pair-level average reaction-time heatmap/table.

## Validation and evidence plan

After human approval of this plan, implementation will be validated from `code/simple_visual_similarity/` with:

- `python experiment.py` for manifest/pair sanity checks.
- `psynet test local` for end-to-end bot completion.
- `psynet simulate` to produce example data for the analysis script/notebook.
- The analysis script/notebook against the simulated or exported data, checking that it creates the required similarity and reaction-time summaries.
- `psynet debug local` plus Playwright/record-participant-video evidence for participant-facing fixation, paired circles, 5-point keyboard/button response, and completion.
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output <absolute attempt evidence path>/performance.json` after functional checks pass.
- Data export to `evidence/data.zip` and a monitor snapshot to `evidence/monitor.html` if the local PsyNet deployment reaches the dashboard state needed for those artifacts.

Final attempt evidence will be saved under `evidence/`, including participant video/screenshots, performance output or a documented blocker, exported data, monitor snapshot, and analysis outputs. If any service-level requirement is blocked by the Cursor Cloud environment, I will record the exact command, failure, and remaining unverified behavior in `EVALUATION.md` rather than treating the check as passed.
