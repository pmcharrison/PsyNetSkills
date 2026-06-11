# Learnings

## Record from the first task page, not from debug setup

The first participant recording started before the participant task and reached
the selector page just as the 150-second capture ended, missing evaluator and
completion evidence. Preparing the browser at the first task page before
starting ffmpeg made the second recording concise enough to cover three trials,
selection, rating, and completion.

*Actions:*
- **PsyNetSkills:** In challenge evidence guidance, emphasize starting participant recordings after setup pages when the setup is not itself part of the evidence. Confidence: medium. Status: considering.

## Keep PsyNet launch-generated files ignored

`psynet test local` failed until `source_code.zip` was added to the experiment
`.gitignore`; local debug also produced `.deploy/`, `dump.rdb`, `Dockertag`, and
`static/assets/`, which should not be committed as attempt source.

*Actions:*
- **PsyNetSkills:** Extend the attempt challenge scaffold reminder to include these local PsyNet generated paths when copying a minimal experiment rather than the full demo template. Confidence: high. Status: considering.

## Separate evaluator experiments and full-browser recordings

Evaluation feedback identified two evidence/design gaps: similarity ratings
should be conducted by an individual experiment rather than embedded in the same
participant flow, and screen recordings must show the full browser viewport and
all generated SVG candidates clearly enough for review.

*Actions:*
- **PsyNetSkills:** Add challenge guidance for independent evaluator tasks to be implemented as a separate runnable experiment when the instructions ask for an independent rating task. Confidence: high. Status: considering.
- **PsyNetSkills:** Update participant-recording guidance to require a quick playback check that all compared stimuli are visible in the saved recording, not just in screenshots. Confidence: high. Status: considering.
