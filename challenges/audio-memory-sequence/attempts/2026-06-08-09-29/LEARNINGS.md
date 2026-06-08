# Learnings

## Timed push buttons fit sequence reproduction

PsyNet's `TimedPushButtonControl` already records ordered button-click events,
which keeps a memory-sequence task simple: trial code can format the event log
into a participant response sequence without custom JavaScript.

*Actions:*
- **PsyNetSkills:** Add this pattern to experiment implementation guidance for future sequence-reproduction challenges. Confidence: high. Status: considering.
- **PsyNet:** Consider documenting `TimedPushButtonControl` as a general ordered-response control, not only a timed-response control. Confidence: medium. Status: considering.

## Dallinger import context hides sibling helpers

`psynet test local` imports the experiment through `dallinger_experiment`, so
plain sibling imports can fail even when `python experiment.py` works locally.

*Actions:*
- **PsyNetSkills:** Update generated experiment guidance to either package helper modules or prepend the experiment directory to `sys.path` before local helper imports. Confidence: high. Status: considering.
- **PsyNet:** Consider documenting the `dallinger_experiment` import context in local testing guidance. Confidence: medium. Status: considering.
