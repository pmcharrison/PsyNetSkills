# Learnings

## Review participant videos for phase visibility, not only screenshots

Screenshots initially showed the intended stimulus states, but video review
caught that response controls were too brief or visible at the wrong time in the
recorded flow. The final evidence needed CSS to hide disabled response controls,
a borderless `GraphicPrompt`, and longer fixation/response dwell times to make
the timing visually auditable.

*Actions:*

- **PsyNetSkills:** Update `psychophysics/SKILL.md` or `record-participant-video/SKILL.md` to remind agents to check participant videos for control visibility across every timed phase, especially when PsyNet controls are disabled but still rendered. Confidence: high. Impact: medium. Status: considering.
- **PsyNetSkills:** Add a note to psychophysics guidance that PsyNet `GraphicPrompt` defaults include a visible border and that borderless white visual fields can be implemented by subclassing the prompt or otherwise setting graphic border styles to none. Confidence: high. Impact: medium. Status: considering.
