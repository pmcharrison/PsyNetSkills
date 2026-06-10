# Learnings

## Typed audio pre-screen assets

PsyNet demos provide reusable volume, headphone, and forced-choice audio screening, but not a ready typed spoken-number check matching this challenge. A local TTS package was needed to create a committed static `five.wav` asset before runtime.

*Actions:*
- **PsyNetSkills:** Add a short note to the audio challenge guidance about acceptable local generation of static prescreen clips when reusable spoken-number assets are unavailable. Confidence: medium. Status: considering.
