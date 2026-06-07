# Learnings

## Avoid running Dallinger from a directory named code

`psynet test local` imports the current experiment directory as a Python package.
When the directory is literally named `code`, Dallinger can collide with
Python's standard-library `code` module before it sees the local package. A
non-conflicting nested experiment directory avoids this.

*Actions:*
- **PsyNetSkills:** Document in the attempt-challenge skill that runnable PsyNet experiments should live in a non-conflicting subdirectory under `code/` when the dashboard schema requires a top-level `code/` folder. Confidence: high. Status: considering.
- **PsyNet:** Consider making Dallinger's experiment package initialization robust to basenames that collide with already-imported stdlib modules. Confidence: medium. Status: considering.
