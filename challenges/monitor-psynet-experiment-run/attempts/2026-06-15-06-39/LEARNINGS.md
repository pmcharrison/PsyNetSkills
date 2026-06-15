# Learnings

## Authorship blocks completed attempt validation

Repository validation allows an in-progress attempt to have an empty `authors` list, but a completed attempt with `ended_at` set needs a human author key. This attempt had to remain metadata-pending because no GitHub username was supplied and the author-identification skill forbids inferring one from runtime context.

*Actions:*

- **PsyNetSkills:** Clarify the attempt-challenge workflow or starter prompt so agents collect the human GitHub author key before closing `ended_at`, or explicitly mark authorship-pending attempts as paused rather than complete. Confidence: high. Impact: medium. Status: considering.
