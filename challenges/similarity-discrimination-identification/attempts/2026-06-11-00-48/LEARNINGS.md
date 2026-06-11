# Learnings

## Psychophysics guidance belongs in a reusable skill

This attempt combines several recurring psychophysics requirements: fixation timing, centered visual layouts, use of PsyNet graphics, use of `StaticNode` metadata, and domain-specific prescreeners such as Ishihara color-vision checks.

*Actions:*
- **PsyNetSkills:** Add a dedicated `psychophysics` skill and point it to PsyNet implementation/evidence skills rather than duplicating their full workflows. Confidence: high. Status: completed. Notes: Added `.cursor/skills/psychophysics/SKILL.md` with fixation, centering, prescreener, metadata, and analysis guidance.

## Prescreeners can be measures rather than exclusion gates

The built-in Ishihara-style `ColorBlindnessTest` excludes participants by default when its performance check fails. For this study, the user clarified that color-vision data should be collected without excluding participants, so the attempt subclasses the PsyNet prescreener to preserve scores while always passing the performance check.

*Actions:*
- **PsyNetSkills:** Note in the psychophysics skill that prescreeners should be configured according to whether the study needs exclusion, stratification, or post hoc covariates. Confidence: high. Status: completed. Notes: The new skill now distinguishes excluding prescreeners from non-excluding measures.

## Evidence profiles should be deliberately short

The first participant evidence attempts took too long because the minimal profile still included many trials and a full Ishihara sequence, and a later multi-segment `ffmpeg` edit on a long raw recording made the VM feel unresponsive. A better pattern is to create a genuinely short evidence profile and record it directly.

*Actions:*
- **PsyNetSkills:** Add psychophysics guidance to keep review profiles representative but short, and prefer direct short recordings over long post-hoc video edits. Confidence: medium. Status: considering.
