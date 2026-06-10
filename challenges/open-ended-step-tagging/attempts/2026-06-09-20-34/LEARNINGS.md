# Learnings

## Attempt template path mismatch

The attempt skill says to use `assets/attempt-template/`, but the templates in this repository are stored under `.cursor/skills/attempt-challenge/assets/attempt-template/`.

*Actions:*

- **PsyNetSkills:** Update the attempt-challenge skill wording to reference its bundled template path, or add a root-level pointer if maintainers want the shorter path. Confidence: high. Status: considering.

## Participant recording needs preinstalled PulseAudio tools

The participant video evidence required `pulseaudio` and `pulseaudio-utils`; they were documented in `AGENTS.md` but not installed in this VM, so recording audio required an apt install and a fresh browser launched against the null sink.

*Actions:*

- **PsyNetSkills:** Consider adding a Cursor Cloud environment setup check for PulseAudio utilities before audio challenge attempts begin. Confidence: medium. Status: completed. Notes: Added skill guidance to test audio as first-class experiment behavior and to launch a fresh browser after PulseAudio routing for evidence recordings.

## Cross-cultural STEP attempts need localization checks

The evaluation identified hardcoded English participant text as the largest gap. A STEP experiment intended for cross-cultural deployment needs participant-facing strings, warnings, and deployment configuration to remain compatible with PsyNet localization and language-specific study variants.

*Actions:*

- **PsyNetSkills:** Add localization expectations to STEP or cross-cultural experiment challenge guidance, including translated instructions and language-specific deployment configuration. Confidence: high. Status: considering.

## Balanced stimulus assignment should still randomize order

The attempt supported culture labels and balanced selection, but selected and presented stimuli deterministically. Future implementations should randomize participant-specific assignment and order while preserving cultural balance constraints.

*Actions:*

- **PsyNetSkills:** Clarify in music-emotion challenge instructions that balanced sampling should include participant-level randomization and should avoid fixed CSV order effects. Confidence: high. Status: considering.

## Music-emotion instructions need research-specific distinctions

The evaluation noted that the participant instructions should distinguish emotions expressed by the music from emotions felt by the listener. This distinction is important for music-emotion data quality and should be explicit in participant-facing prose.

*Actions:*

- **PsyNetSkills:** Add an instruction-quality checklist item for music-emotion challenges that asks agents to preserve expressed-versus-felt emotion wording when the source study depends on that distinction. Confidence: medium. Status: considering.

## Quality-control checks improve tag data

The reviewer recommended a comprehension check and headphone screening to reduce genre labels, lyrics, non-emotion responses, and low-quality audio-listening data.

*Actions:*

- **PsyNetSkills:** Include comprehension checks and headphone screening as expected quality-control features for audio tagging challenges unless the public instructions explicitly exclude them. Confidence: medium. Status: considering.
