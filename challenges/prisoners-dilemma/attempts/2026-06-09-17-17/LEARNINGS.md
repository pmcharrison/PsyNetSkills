# Learnings

## Re-attempts benefit from distinct game mechanics

Using a different partner strategy for the second attempt made the implementation
less of a duplicate while still satisfying the same public challenge brief.

*Actions:*
- **PsyNetSkills:** Consider noting in challenge attempt guidance that reruns should vary substantive design choices when the public brief allows it. Confidence: low. Status: considering.

## Recording output paths should be absolute

Reusing a tmux recording session can preserve an older working directory. The
participant video should be written with an absolute evidence path to avoid
placing the MP4 in a previous attempt's folder.

*Actions:*
- **PsyNetSkills:** Update participant-recording guidance to prefer absolute output paths when recording from reusable tmux sessions. Confidence: high. Status: considering.

## Performance evidence should be interpreted, not just collected

Human evaluation noted that the 40-bot performance test had many incomplete
bots, about a 50% success rate, despite zero explicit bot or request errors. The
dashboard network visualization was also empty, which made the monitoring
evidence less informative for a repeated-game experiment implemented without
network nodes.

*Actions:*
- **PsyNetSkills:** Encourage attempt writeups to call out low completion rates and empty dashboard network views as evidence limitations rather than treating artifact presence as sufficient. Confidence: high. Status: considering.
