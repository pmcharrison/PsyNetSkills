# Learnings

## Standard PsyNet ignore entries

PsyNet local debug requires `.gitignore` to exist and asks for `source_code.zip`
to be ignored. It can also create a machine-specific `static/assets` symlink
pointing to the local PsyNet asset cache.

*Actions:*
- **PsyNetSkills:** Consider adding a reusable minimal PsyNet experiment
  `.gitignore` snippet to the attempt guidance. Confidence: high. Impact: low. Status:
  considering.
## Export paths and source-code prompts

`psynet export local` behaved more reliably with an absolute evidence path.
Without `--no-source`, local export prompted for dashboard credentials when
trying to download source code; this is unnecessary when the attempt source is
already committed under `code/`.

*Actions:*
- **PsyNetSkills:** Consider documenting absolute export paths and `--no-source`
  for local attempt evidence exports. Confidence: medium. Impact: low. Status: considering.
## Evidence quality needs stricter interpretation

The evaluator found that the participant video did not convincingly show an
agent attempting the experiment, and the performance test was overstated despite
only 4 of 44 started bots succeeding.

*Actions:*
- **PsyNetSkills:** Consider requiring attempt summaries to report bot
  completion counts alongside error counts, and to treat low-completion
  performance tests as weak evidence even when request errors are zero.
  Confidence: high. Impact: high. Status: considering.
- **PsyNetSkills:** Consider adding an evidence-review checkpoint that verifies
  participant recordings show meaningful task progression before they are
  described as successful. Confidence: high. Impact: high. Status: considering.
