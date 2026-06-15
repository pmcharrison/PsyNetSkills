# Simple visual discrimination experiment

This PsyNet experiment implements a 10-trial same-different color discrimination task.

## Local checks

Run from this directory with the PsyNet virtual environment active:

- `python experiment.py`
- `psynet test local`
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0 --json-output ../../evidence/performance.json`

The participant sees a 500 ms fixation cross, two colored circles for 1000 ms, a 500 ms blank display, then Same/Different response options. The keyboard shortcuts are `F` for Same and `J` for Different.
