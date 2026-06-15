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

## Keep concise task guidance and neutral UI chrome in psychophysics trials

The evaluator found the original per-trial display confusing after all trial
instruction text was removed. Psychophysics guidance says not to add labels
inside the stimulus area, but concise task guidance outside the visual field can
still be important. The evaluator also noted that the progress bar must follow
the same neutral gray treatment as buttons in color-sensitive tasks.

*Actions:*

- **PsyNetSkills:** Update `psychophysics/SKILL.md` to clarify that agents should avoid text inside the stimulus area while still preserving concise per-trial task instructions outside the stimulus field when the task would otherwise be ambiguous. Confidence: high. Impact: medium. Status: completed.
- **PsyNetSkills:** Update `psychophysics/SKILL.md` to mention PsyNet's default top progress bar color and instruct agents to neutralize progress-bar styling alongside buttons for color-related experiments. Confidence: high. Impact: medium. Status: completed.
