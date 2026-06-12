# Learnings

## Prefer flattened PsyNet export columns for repeated objects

PsyNet simulated exports can serialize repeated nested objects with JSON reference markers such as `py/id`, while the same table may also provide flattened columns for trial-level fields. The analysis script initially read only the nested `definition` JSON and failed on self-pairs until it preferred the flattened `stimulus_a` and `stimulus_b` columns.

*Actions:*

- **PsyNetSkills:** Update experiment-analysis guidance to recommend preferring flattened export columns over nested JSON definitions when both are present in PsyNet CSV exports. Confidence: high. Impact: medium. Status: considering.

## Use PsyNet Graphics for simple psychophysics displays

The final implementation used custom HTML/SVG/JavaScript/CSS for a simple visual psychophysics task even though the psychophysics guidance points toward PsyNet Graphics/Raphael. The resulting participant-facing behavior worked, but the implementation style was less consistent with the expected PsyNet-native approach.

*Actions:*

- **PsyNetSkills:** Strengthen the psychophysics and experiment-implementation guidance so agents default to PsyNet Graphics/Raphael for simple geometric stimuli, and require a short justification before replacing it with custom HTML/SVG/JavaScript/CSS. Confidence: high. Impact: medium. Status: considering.

## Do not invent missing reaction-time data

The implementation used an arbitrary fallback reaction time for bot or missing event-log paths to keep automated checks passing. This is poor practice because it silently turns missing timing evidence into fabricated data.

*Actions:*

- **PsyNetSkills:** Add guidance that bot tests should either provide realistic event metadata or assert missing reaction-time handling explicitly; agents must not impute arbitrary reaction-time values in production experiment answers. Confidence: high. Impact: high. Status: considering.
- **PsyNet:** Consider documenting a standard bot-response pattern for controls that need event-log-derived reaction times, so simulated participants can exercise timing-dependent answer formatting without fabricated fallback values. Confidence: medium. Impact: medium. Status: considering.
