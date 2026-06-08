---
score:
---

# Evaluation

## Summary

Summarize the human evaluator's overall judgment.

## Strengths

- 

## Weaknesses

- 

## Criteria

If `CRITERIA.md` is present, ask the evaluator about each criterion and record
the result here.

- [ ] The participant hears or otherwise receives a clear tone sequence before
  responding.
- [ ] The response interface allows ordered sequence reproduction.
- [ ] Target and response sequences are saved in analyzable form.
- [ ] The implementation handles at least four trials without manual repetition
  in the code where a PsyNet trial abstraction would be clearer.
- [ ] Evidence demonstrates that the trial flow can be exercised locally.

## Notes

- Score and feedback should come from a human evaluator, captured
  conversationally when working with Cursor Cloud Agents.
- Evidence note: `evidence/participant.mp4` shows the participant-facing flow
  through completion with captured browser audio. This required installing
  PulseAudio, creating a null sink, launching Chrome with that sink as its audio
  target, and recording `psynet_rec.monitor` with `ffmpeg`.
