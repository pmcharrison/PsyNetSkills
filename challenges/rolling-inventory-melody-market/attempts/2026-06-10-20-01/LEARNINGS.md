# Learnings

## Typed audio pre-screen assets

PsyNet demos provide reusable volume, headphone, and forced-choice audio screening, but not a ready typed spoken-number check matching this challenge. A local TTS package was needed to create a committed static `five.wav` asset before runtime.

*Actions:*
- **PsyNetSkills:** Add a short note to the audio challenge guidance about acceptable local generation of static prescreen clips when reusable spoken-number assets are unavailable. Confidence: medium. Status: considering.

## Reference wording and styling are parity requirements

When a challenge asks to preserve an existing experiment except for domain-specific substitutions, participant-facing microcopy and UI styling should remain identical unless the domain change forces a difference. In this attempt, the popularity-rating labels and "New" styling diverged from the reference more than the evaluator expected.

*Actions:*
- **PsyNetSkills:** Add a reminder to experiment implementation guidance that reference-replication challenges require exact participant-facing phrasing and styling by default, with documented exceptions only for necessary domain substitutions. Confidence: high. Status: considering.
