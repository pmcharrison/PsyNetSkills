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
- **PsyNetSkills:** Add psychophysics guidance to keep review profiles representative but short, and prefer direct short recordings over long post-hoc video edits. Confidence: medium. Status: completed. Notes: The psychophysics skill now warns against long post-hoc video edits, but evaluation feedback clarified that a profile can also be too short and unrepresentative.

## Psychophysics evidence must show representative task structure

The evaluation rejected a one-trial-per-block video as too short and too fast. Review evidence should demonstrate a sensible abbreviated experiment, such as three trials per block, while keeping prescreeners and demographics efficient.

*Actions:*
- **PsyNetSkills:** Update psychophysics evidence guidance to use enough trials per block to demonstrate the task structure, not just one token trial. Confidence: high. Status: completed.

## Visual timing and layout need explicit review

The evaluation identified two core psychophysics UI failures: the fixation cross remained visible during stimulus presentation, and the similarity rating scale was not centered. These are participant-facing design failures even when the code runs and records data.

*Actions:*
- **PsyNetSkills:** Add explicit visual review checks that fixation disappears before stimuli appear, stimuli/controls are centered, and recordings show a single centered browser window. Confidence: high. Status: completed.

## Performance evidence should consider completion rate

The performance run had low bot completion despite zero request errors. Future attempts should not present such a run as healthy without explaining the completion-rate problem or adjusting the performance-test duration/profile.

*Actions:*
- **PsyNetSkills:** Add guidance that psychophysics performance evidence should include bot completion rate, not just request error rate. Confidence: high. Status: completed.
