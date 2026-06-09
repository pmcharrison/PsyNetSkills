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
