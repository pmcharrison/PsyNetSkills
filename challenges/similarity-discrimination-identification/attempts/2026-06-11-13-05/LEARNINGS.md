# Learnings

## Six stimuli are required for N=5 lure trials

The first manifest draft had only five colors, which cannot support a
probe-absent lure when the display set size is five. The corrected design uses
six colors so every N=5 absent-probe trial has an out-of-display lure.

*Actions:*
- **PsyNetSkills:** Add a reminder to the psychophysics or attempt guidance that variable-set identification tasks need at least `max_set_size + 1` stimuli when probe-absent lures are required. Confidence: high. Status: considering.

## PsyNet local tests expect the standard `test.py`

The first `psynet test local` run failed before launching the experiment because
the generated attempt omitted PsyNet's standard `test.py` wrapper. Copying only
`experiment.py` and config files is not enough for local test orchestration.

*Actions:*
- **PsyNetSkills:** Keep the attempt-challenge reminder to copy standard experiment support files, and consider naming `test.py` alongside `.gitignore` in that checklist. Confidence: high. Status: considering.
