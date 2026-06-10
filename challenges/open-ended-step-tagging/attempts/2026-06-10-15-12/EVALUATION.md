---
score:
---

# Evaluation

Not yet evaluated by a human reviewer.

## Criteria checklist

- [x] The experiment implements the open-ended STEP tagging phase rather than only a conventional fixed-choice rating task.
- [x] Participants can listen to 15-second clips, add multiple single-word tags, rate previously contributed tags, and flag invalid tags.
- [x] Existing tags are persisted per stimulus and become available to later participants, allowing iterative refinement over repeated participant passes.
- [x] The implementation records enough structured data to reconstruct submitted tags, ratings, flags, participant or trial order, and stimulus identifiers.
- [x] The participant-facing instructions clearly forbid genre labels and lyric transcription, enforce or validate the 15-character single-word constraint, and invite native-language emotion or affect descriptors.
- [x] The stimulus setup is reproducible locally without external credentials or copyrighted downloads, while still making clear how to replace the demo audio with real study stimuli.
- [x] The sampling logic supports balanced presentation across at least three culture labels and a participant workload close to 15 clips when enough clips are available.
- [x] The attempt includes local run instructions and evidence that the generated, rated, and flagged tags are stored correctly.
- [x] The attempt does not implement unrelated downstream stages as the main focus, such as the separate tag emotionality validation or dense-rating experiment, except for documenting how STEP output would feed those stages.

## Validation notes

- `psynet translate de` successfully extracted `locales/experiment.pot` with 18 entries, then stopped before writing German translations because no local OpenAI API key is configured. No production credentials were added.
- `supported_locales` is committed as `["en"]` so local launch does not require an unavailable German `.po`; add `de` after generating `locales/de/LC_MESSAGES/experiment.po`.
- `psynet test local` passed after bot trials completed and saved structured STEP tagging answers.
- A local duration check confirmed all six generated demo WAV files are 15.0 seconds.
