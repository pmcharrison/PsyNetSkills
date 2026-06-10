# Learnings

## Standard PsyNet ignore entries

PsyNet local debug requires `.gitignore` to exist and asks for `source_code.zip`
to be ignored. It can also create a machine-specific `static/assets` symlink
pointing to the local PsyNet asset cache.

*Actions:*
- **PsyNetSkills:** Consider adding a reusable minimal PsyNet experiment
  `.gitignore` snippet to the attempt guidance. Confidence: high. Status:
  considering.

## Export paths and source-code prompts

`psynet export local` behaved more reliably with an absolute evidence path.
Without `--no-source`, local export prompted for dashboard credentials when
trying to download source code; this is unnecessary when the attempt source is
already committed under `code/`.

*Actions:*
- **PsyNetSkills:** Consider documenting absolute export paths and `--no-source`
  for local attempt evidence exports. Confidence: medium. Status: considering.
