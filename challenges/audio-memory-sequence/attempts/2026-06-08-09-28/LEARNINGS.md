# Learnings

## JSSynth is a good fit for labeled tone sequences

The challenge does not require pre-recorded audio files. PsyNet's `JSSynth` with `Note`
objects provides deterministic low/medium/high tones in the browser and keeps the
attempt self-contained.

*Actions:*
- **PsyNetSkills:** Mention `JSSynth` as the default approach for simple tone-memory
  challenges in the experiment-implementation skill. Confidence: high. Status:
  considering.
- **PsyNet:** No change needed. Confidence: high. Status: dismissed.

## TimedPushButtonControl captures ordered reproduction

`TimedPushButtonControl` records an event log of button presses, which can be reduced
to the participant's response sequence. Pairing it with a listen page that disables
playback controls matches the memory-task guidance.

*Actions:*
- **PsyNetSkills:** Add a short pattern note for sequence reproduction trials using
  `TimedPushButtonControl.format_answer`. Confidence: medium. Status: considering.
- **PsyNet:** No change needed. Confidence: high. Status: dismissed.

## Legacy export avoids dashboard credential prompts

`psynet export local --legacy --no-source` exported bot data without interactive
dashboard credentials, which is useful in headless cloud environments.

*Actions:*
- **PsyNetSkills:** Document `--legacy --no-source` in attempt evidence guidance.
  Confidence: high. Status: considering.
- **PsyNet:** No change needed. Confidence: high. Status: dismissed.
