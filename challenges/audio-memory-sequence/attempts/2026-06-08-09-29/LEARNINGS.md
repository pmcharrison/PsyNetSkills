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

## Keep PsyNet config in one place

PsyNet rejects config variables declared both in `config.txt` and on the
experiment class. Small generated experiments should choose one source of truth.

*Actions:*
- **PsyNetSkills:** Add a reminder to generated experiment templates to avoid duplicating config keys across files. Confidence: high. Status: considering.
- **PsyNet:** The current error is clear enough; no framework change suggested. Confidence: medium. Status: dismissed.

## Constraints file is part of local PsyNet validation

`psynet test local` checks Python dependencies through `constraints.txt`, so a
minimal experiment folder with only `requirements.txt` is not enough.

*Actions:*
- **PsyNetSkills:** Include `dallinger constraints generate` in the experiment-attempt setup checklist. Confidence: high. Status: considering.
- **PsyNet:** Consider having `psynet test local` explain how to generate missing constraints. Confidence: medium. Status: considering.

## Ignore generated PsyNet archive state

PsyNet local launch writes archive/deployment files and explicitly requires
`source_code.zip` to be ignored before continuing.

*Actions:*
- **PsyNetSkills:** Add `.deploy/` and `source_code.zip` to generated PsyNet experiment `.gitignore` files. Confidence: high. Status: considering.
- **PsyNet:** Current preflight reports the missing ignore clearly. Confidence: medium. Status: dismissed.
