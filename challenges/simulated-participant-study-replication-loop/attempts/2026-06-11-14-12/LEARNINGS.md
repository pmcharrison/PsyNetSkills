# Learnings

## PsyNet experiment package imports

Dallinger loaded the attempt experiment as a package during `psynet test local`,
so a bare sibling import such as `from stimuli import ...` failed even though
direct script execution worked.

*Actions:*
- **PsyNetSkills:** Add a note to the experiment implementation skill that attempt experiments with helper modules should use package-safe imports or a documented fallback for direct script execution. Confidence: high. Status: considering.

## Constraints are required for launched PsyNet checks

`psynet test local` launched the experiment only after `constraints.txt` was
generated from the pinned `requirements.txt`. A missing constraints file produced
a launch-time `FileNotFoundError`.

*Actions:*
- **PsyNetSkills:** Add `dallinger constraints generate` to the pre-launch checklist for generated attempt experiments that include `requirements.txt`. Confidence: high. Status: considering.

## GUI-agent recordings can be too slow for short participant evidence

The browser-driving agent completed the participant flow correctly, but two
ffmpeg recordings hit the three-minute cap before reaching completion. Direct
`xdotool` automation provided a concise recording while screenshots documented
instructions and representative states.

*Actions:*
- **PsyNetSkills:** Extend the `record-participant-video` skill with a fast-path recipe for simple button-based PsyNet flows using `xdotool` after one manual dry run verifies the tab/click sequence. Confidence: medium. Status: considering.

## Simulated evidence needs explicit scope

The human evaluation emphasized that mock participant profiles validate the
workflow and simulation behavior, not real human memory or real LLM participant
behavior.

*Actions:*
- **PsyNetSkills:** Keep challenge reports and evaluation templates explicit that simulated participant results are workflow/simulation evidence, not human-subject or real-provider behavioral evidence unless those external populations or providers were actually tested. Confidence: high. Status: considering.
