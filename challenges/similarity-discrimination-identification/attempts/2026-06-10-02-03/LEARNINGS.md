# Learnings

## Client-side blocks improve performance evidence

The first retry still under-completed the 40-bot performance test when each task
trial was a separate PsyNet page. Grouping many short visual trials into one
client-side block page preserved per-trial metadata and reaction times while
reducing server page transitions enough for many replacement bots to complete
within the fixed 5-minute performance window.

*Actions:*
- **PsyNetSkills:** Consider documenting client-side block pages as an option
  for high-trial-count visual tasks, with a warning that exported data must
  reconstruct trial-level rows explicitly. Confidence: medium. Impact: medium. Status:
  considering.
## Page-level progress can mislead for block pages

PsyNet's page-level progress bar froze or jumped during multi-trial client-side
blocks because many participant-visible trials happened within a single PsyNet
page. The final retry disables the progress bar to avoid misleading evidence.

*Actions:*
- **PsyNetSkills:** Consider adding a review checklist item for whether progress
  indicators remain meaningful when custom client-side trial loops are used.
  Confidence: high. Impact: medium. Status: considering.
## Non-excluding color-vision checks for end questionnaires

The participant video initially terminated before demographics after the
Ishihara module. Setting the color-vision threshold to zero kept the measure in
the flow without excluding participants before required end questionnaires.

*Actions:*
- **PsyNetSkills:** Consider advising challenge attempts to make end-of-study
  screening measures non-excluding unless exclusion is explicitly required by
  the challenge. Confidence: medium. Impact: medium. Status: considering.
## Fixation alignment needs visual review

The evaluator found that the fixation cross was centered relative to the whole
page content rather than the stimulus display region, and that multi-item
identification showed two fixation crosses.

*Actions:*
- **PsyNetSkills:** Consider adding a participant-video review item that checks
  fixation alignment against the stimulus display area, not against surrounding
  question text or controls. Confidence: high. Impact: high. Status: considering.
## Analysis evidence should include plots

CSV summaries were useful but not enough for review; the evaluator requested
visualizations of response distributions and similarity matrices.

*Actions:*
- **PsyNetSkills:** Consider recommending both table and image outputs for
  analysis evidence in experiment implementation attempts. Confidence: medium. Impact: high. Status: considering.
