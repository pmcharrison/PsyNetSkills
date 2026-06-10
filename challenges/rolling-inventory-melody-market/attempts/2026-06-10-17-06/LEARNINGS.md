# Learnings

## Standard PsyNet support files matter

Copying only `experiment.py`, templates, and a minimal config was not enough for
all PsyNet commands. `psynet test local` needed the standard `test.py` harness,
dependency pre-checks needed `constraints.txt`, and legacy debug launch needed
`.python-version`.

*Actions:*

- **PsyNetSkills:** Extend the attempt-challenge support-file reminder to name `test.py`, `constraints.txt`, and `.python-version` alongside `.gitignore` for runnable PsyNet experiments. Confidence: high. Status: considering.
