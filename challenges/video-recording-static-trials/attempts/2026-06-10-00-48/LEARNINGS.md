# Learnings

## S3-centered attempts need a safe credential workflow

This attempt correctly avoided a local upload stub, but could not complete the
challenge because the environment had no approved S3/AWS configuration and the
repository policy forbids committing or publishing custom service credentials.

*Actions:*
- **PsyNetSkills:** Consider adding a documented workflow for challenges whose
  central requirement is an external service: e.g., approved ephemeral test
  buckets, credential injection rules, and required redaction/evidence handling.
  Confidence: high. Impact: high. Status: considering.
