# Report

## Implementation

The attempt implements a generator-based PsyNet experiment in `code/autocog_compatible_human_dm_task/`. The generator accepts a Python config file containing a dictionary named `config`, validates the required fields, expands paired option ratings into complete integer repetitions up to `max_trials`, and writes a runnable experiment to `code/generated_experiment/`.

The generated experiment uses `StaticNode`, `StaticTrial`, and `StaticTrialMaker` to administer 50 forced-choice trials. Each trial displays two options side by side, with five rating rows showing the rating label, validity, and displayed option value. Choices are saved as language-neutral option IDs while exported data retain validities, original option ratings, source pair index, presentation swap flag, and left/right option identities.

## Translation readiness

Participant-facing strings are marked with PsyNet's translation helper using the explicit `experiment` namespace. The generated experiment includes English source text plus manually reviewed Hindi and German PO files, and `psynet translate hi de` completes without translation-service credentials. Numeric config values, option IDs, trial indices, and exported data keys remain language-neutral.

## Validation

Generator unit tests cover trial expansion and malformed config rejection. `python3 experiment.py` verifies the generated trial definitions load. `psynet test local` launches the generated experiment and drives bots through the full participant flow. `psynet simulate` produces a 12-bot export containing 600 completed `ChoiceTrial` rows.

The required 40-bot, 5-minute `psynet performance-test local` completed and wrote `evidence/performance.json`. It reported no bot errors and no request errors, but all 40 bots were still incomplete at the fixed 5-minute cutoff. This is recorded as performance evidence rather than a complete high-load completion result.

## Evidence

- `evidence/participant.mp4` combines English, Hindi, and German participant-flow recordings.
- `evidence/participant_en.mp4`, `evidence/participant_hi.mp4`, and `evidence/participant_de.mp4` provide locale-specific recordings.
- `evidence/screenshots/` contains targeted ad, welcome, instructions, choice, and completion screenshots for all three locales.
- `evidence/simulated_data.zip` and `evidence/data.zip` contain exported simulated data.
- `evidence/analyses/analysis.ipynb` reads the exported CSVs directly and compares choices with tallying and WADD predictions.
- `evidence/performance.json` contains the required load-test output.
- `evidence/monitor.html` contains a local debug dashboard snapshot.

## Findings

The implementation meets the generator, trial-display, translation, data-saving, simulation, and participant-flow requirements. The only notable caveat is that the fixed 5-minute, 40-bot performance test did not allow bots to complete the full 50-trial task under load, although it recorded stable request metrics with zero bot or request errors.
