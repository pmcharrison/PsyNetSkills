# Learnings

## Attempt template path mismatch

The attempt skill says to use `assets/attempt-template/`, but the templates in this repository are stored under `.cursor/skills/attempt-challenge/assets/attempt-template/`.

*Actions:*

- **PsyNetSkills:** Update the attempt-challenge skill wording to reference its bundled template path, or add a root-level pointer if maintainers want the shorter path. Confidence: high. Status: considering.

## Participant recording needs preinstalled PulseAudio tools

The participant video evidence required `pulseaudio` and `pulseaudio-utils`; they were documented in `AGENTS.md` but not installed in this VM, so recording audio required an apt install and a fresh browser launched against the null sink.

*Actions:*

- **PsyNetSkills:** Consider adding a Cursor Cloud environment setup check for PulseAudio utilities before audio challenge attempts begin. Confidence: medium. Status: considering.
