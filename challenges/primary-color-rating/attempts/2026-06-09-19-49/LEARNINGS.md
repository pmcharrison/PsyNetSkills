# Learnings

## Standalone PsyNet experiments need generated scaffold files

`psynet test local` fails before launch if a standalone experiment directory is missing PsyNet's generated `.gitignore`, even when the Python experiment itself is valid.

*Actions:*
- **PsyNetSkills:** Consider adding a minimal PsyNet experiment scaffold checklist to the experiment implementation skill or attempt template. Confidence: medium. Status: considering. Notes: This would prevent agents from copying only `experiment.py`, `config.txt`, and test files.
