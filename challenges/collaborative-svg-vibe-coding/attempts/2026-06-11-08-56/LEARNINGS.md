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
