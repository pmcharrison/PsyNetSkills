# Criteria

Evaluators should check the completed attempt against these points:

- The experiment implements the open-ended STEP tagging phase rather than only a
  conventional fixed-choice rating task.
- Participants can listen to 15-second clips, add multiple single-word tags,
  rate previously contributed tags, and flag invalid tags.
- Existing tags are persisted per stimulus and become available to later
  participants, allowing iterative refinement over repeated participant passes.
- The implementation records enough structured data to reconstruct submitted
  tags, ratings, flags, participant or trial order, and stimulus identifiers.
- The participant-facing instructions clearly forbid genre labels and lyric
  transcription, enforce or validate the 15-character single-word constraint, and
  invite native-language emotion or affect descriptors.
- The stimulus setup is reproducible locally without external credentials or
  copyrighted downloads, while still making clear how to replace the demo audio
  with real study stimuli.
- The sampling logic supports balanced presentation across at least three
  culture labels and a participant workload close to 15 clips when enough clips
  are available.
- The attempt includes local run instructions and evidence that the generated,
  rated, and flagged tags are stored correctly.
- The attempt does not implement unrelated downstream stages as the main focus,
  such as the separate tag emotionality validation or dense-rating experiment,
  except for documenting how STEP output would feed those stages.
