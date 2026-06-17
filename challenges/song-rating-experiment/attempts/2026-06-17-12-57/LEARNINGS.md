# Learnings

## Audio prescreen evidence needs a deterministic runner path

Manual browser agents can verify that audio controls render and become enabled,
but they cannot reliably hear tones and answer a hearing prescreen as a human
would. A Playwright evidence runner should either infer the correct answer from
test metadata or use a documented visual-review profile while separate
functional checks validate the real audio-gated path.

*Actions:*

- **PsyNetSkills:** Update `record-participant-video` guidance to mention audio
  prescreens whose correct answers depend on hearing, recommending a documented
  deterministic evidence-runner strategy plus an explicit note that simulated or
  scripted answers are not human hearing evidence. Confidence: high. Impact:
  medium. Status: considering.
- **PsyNetSkills:** Update `prepare-experiment-tunnel` guidance for audio
  experiments to require a human-facing tunnel smoke test that verifies audible
  playback and usable Replay/Next controls through the public URL before handing
  off links. Confidence: high. Impact: high. Status: considering.
