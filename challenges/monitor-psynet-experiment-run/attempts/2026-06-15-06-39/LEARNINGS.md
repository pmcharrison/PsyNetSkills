# Learnings

## Keep attempt status notes synchronized with metadata fixes

Repository validation allows an in-progress attempt to have an empty `authors` list, but a completed attempt with `ended_at` set needs a human author key. This attempt originally had to remain metadata-pending because no GitHub username was supplied and the author-identification skill forbids inferring one from runtime context. After the metadata was completed, some attempt notes still described authorship as pending, which made the evidence less tidy even though `agent.json` was complete.

*Actions:*

- **PsyNetSkills:** Clarify the attempt-challenge workflow or starter prompt so agents collect the human GitHub author key before closing `ended_at`, or explicitly mark authorship-pending attempts as paused rather than complete. Confidence: high. Impact: medium. Status: considering.
- **PsyNetSkills:** When an agent resolves a metadata blocker after an attempt has already written timeline, monitoring, or learning notes, update those status-dependent notes in the same commit so the final evidence does not keep stale "pending" statements. Confidence: high. Impact: low. Status: considering.
- **PsyNetSkills:** For operations-only challenges that do not generate experiment code, create explicit placeholder or summary files under the standard `code` and `evidence` attempt entries before closing the attempt, so `psynetsk-validate` can distinguish "not applicable" from missing artifacts. Confidence: high. Impact: medium. Status: considering.
