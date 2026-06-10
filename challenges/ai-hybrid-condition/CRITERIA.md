# Criteria

- The implementation cleanly separates human participants, AI participants, and
  hybrid runs while preserving a shared experimental data model.
- The modified experiment does not change the original Gibbs Sampling with
  People logic when the configured AI proportion is 0%.
- Human and AI experiment flows are consistent: assignment, trial order,
  stimulus metadata, response recording, and downstream sampling behavior remain
  comparable across conditions.
- The AI prompt or policy is designed to match the experiment instructions given
  to human participants.
- Stimuli are presented consistently to human and AI participants, with the same
  stimulus identifiers and decision-relevant information available in both
  conditions.
- The configured AI proportion can span the full 0%-100% range and produces
  inspectable participant-condition assignments.
- Evidence includes clear testing of pure-human, pure-AI, and at least one
  mixed human-AI configuration.
- Testing demonstrates that saved data can distinguish human and AI responses
  without breaking analyses that depend on the original experiment structure.
