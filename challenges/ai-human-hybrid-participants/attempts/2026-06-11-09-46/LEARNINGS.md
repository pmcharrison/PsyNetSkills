# Learnings

## Keep helper tests out of SQLAlchemy experiment imports

Importing `experiment.py` from helper tests can register custom SQLAlchemy tables
twice under `psynet test local`, because PsyNet loads the experiment module
through its own package path. Moving pure helper logic into `hybrid.py` let both
unit tests and the experiment share code without re-importing the SQL models.

*Actions:*
- **PsyNetSkills:** Consider documenting this pattern for challenge attempts that add unit tests around PsyNet experiments with custom tables. Confidence: medium. Status: considering.

## Use absolute paths for PsyNet export evidence

`psynet export local` resolves relative `--path` values from the deployment
context during local debug runs, not necessarily from the shell's current
experiment directory. An absolute attempt evidence path avoided permission and
parent-directory errors.

*Actions:*
- **PsyNetSkills:** Consider updating experiment evidence guidance to recommend absolute paths for `psynet export local --path` in Cursor Cloud attempts. Confidence: high. Status: considering.
