# Learnings

## Repeat trials reuse static definitions

Static repeat trials inherit the parent trial definition, which can accidentally
reuse per-trial metadata such as recording IDs. This attempt avoids repeat
trials in the demo so every recording-enabled trial has a unique backend hash.

*Actions:*
- **PsyNetSkills:** Consider documenting this caveat in challenges that require
  trial-specific identifiers. Confidence: medium. Status: considering.

## Dashboard monitor data expects JSON-serializable records

`get_basic_data(context="monitor")` is rendered by the dashboard as JSON, while
exports can consume data frames. Returning record dictionaries for monitor
context avoids a dashboard serialization error without changing exported CSVs.

*Actions:*
- **PsyNetSkills:** Add a note to experiment-attempt guidance that dashboard
  monitor snapshots can exercise a different `get_basic_data` serialization path
  than exports. Confidence: medium. Status: considering.

## Local upload stubs are not enough for S3-centered challenges

The evaluator judged the local/test upload path and simulated 197-byte files as
an experimental stub, not a real implementation of the challenge. When the core
task is S3 streaming and bucket preparation, the attempt should either exercise
real S3 with user-provided local credentials or clearly stop and ask for a safe
credential workflow instead of presenting local placeholders as sufficient.

*Actions:*
- **PsyNetSkills:** Update challenge-attempt guidance to require explicit
  evidence for real external-service integration when it is the central
  challenge requirement, or to record a blocker before substituting a local stub.
  Confidence: high. Status: considering.
