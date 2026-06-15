# Learnings

## Make stimulus downloads retryable

Wikimedia Commons returned a temporary 429 while preparing image stimuli; an idempotent downloader with backoff made the attempt reproducible without manual cleanup.

*Actions:*
- **PsyNetSkills:** Consider mentioning retryable/idempotent stimulus preparation in experiment implementation challenge guidance when public web assets are required. Confidence: medium. Impact: medium. Status: considering.
