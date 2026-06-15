# Learnings

## Fixation belongs to the stimulus stage

Centering fixation relative to the full page made it vulnerable to question text
and response controls. The follow-up fixes this by rendering fixation, memory
displays, blank delay, and probes in the same fixed-size stimulus stage, with
instructions and buttons below the stage.

*Actions:*
- **PsyNetSkills:** Consider recommending a fixed stimulus stage for visual
  timing tasks so fixation and stimuli share the same coordinate frame.
  Confidence: high. Impact: high. Status: considering.
## Block-level timing needs video-readable phases

The first follow-up video had correct centering but block 3 phases were too
short to verify reliably. Longer display/delay durations and an explicit delay
caption made the sequence reviewable without moving the stimulus stage.

*Actions:*
- **PsyNetSkills:** Consider advising attempts to make evidence recordings
  slightly slower than the minimal functional path when timing phases are part
  of the task requirements. Confidence: medium. Impact: medium. Status: considering.
## Analysis artifacts should include figures

CSV tables alone did not satisfy review needs for this challenge. The follow-up
adds SVG visualizations for the similarity matrix, response distributions,
discrimination accuracy, and reaction times.

*Actions:*
- **PsyNetSkills:** Consider listing figure outputs alongside CSV outputs in the
  experiment implementation evidence checklist when the challenge requests an
  analysis script. Confidence: medium. Impact: high. Status: considering.
