# Learnings

## GraphicPrompt frame behavior needs browser evidence

A bot-only `psynet test local` run passed while the first browser recording showed `GraphicPrompt` frames not clearing/activating response controls as intended. The fix used native `ModularPage` and `PushButtonControl` with a small timed HTML/JS prompt.

*Actions:*
- **PsyNetSkills:** Add a reminder to experiment implementation guidance that timed visual-frame behavior must be checked in a browser recording, not only with bots. Confidence: high. Status: considering.
- **PsyNet:** Consider documenting common pitfalls when `GraphicPrompt` frame sequencing is used with response controls. Confidence: medium. Status: considering.

## Randomized Ishihara order complicates scripted evidence

Supplying fixed Ishihara answers in a manual recording failed when plate order was randomized. Minimal evidence mode now relaxes the threshold while still administering the pages; the default profile keeps the normal threshold.

*Actions:*
- **PsyNetSkills:** Document that participant evidence scripts should inspect the displayed Ishihara plate rather than assume the default answer order. Confidence: high. Status: considering.
