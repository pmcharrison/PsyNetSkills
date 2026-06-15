# Learnings

## PsyNet custom config values must not be duplicated

PsyNet launch prechecks reject custom config keys when the same key is defined
in both `experiment.py` defaults and `config.txt`. For experiment attempts that
need documented, user-editable settings, register custom keys in
`extra_parameters`, put values in `config.txt`, and keep `experiment.py`
defaults out of the duplicated-key path.

*Actions:*
- **PsyNetSkills:** Add a brief reminder to experiment implementation guidance that custom config keys should be registered in `extra_parameters` and defined in either `config.txt` or `experiment.py`, but not both. Confidence: high. Impact: medium. Status: considering.
