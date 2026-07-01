# Learnings

## S3-centered attempts need a safe credential workflow

This attempt correctly avoided a local upload stub, but could not complete the
challenge because the environment had no approved S3/AWS configuration and the
repository policy forbids committing or publishing custom service credentials.
The evaluation clarified that future attempts also need a better path for
non-accessible S3 buckets, not just a fail-fast missing-credentials blocker.

*Actions:*
- **PsyNetSkills:** Consider adding a documented workflow for challenges whose
  central requirement is an external service: e.g., approved ephemeral test
  buckets, credential injection rules, and required redaction/evidence handling.
  Confidence: high. Impact: high. Status: considering. Notes: Evaluation score
  5/10; future guidance should include how to handle inaccessible S3 buckets.
