# Learnings

## Generator challenges need explicit generated-output evidence

This challenge asks the agent to implement a generator that consumes a Python config and emits a runnable PsyNet experiment. The standard experiment evidence checklist still applies, but the attempt plan must also demonstrate that the generator itself was invoked from the example config and that the generated experiment, not a hand-written bypass, produced the participant-flow evidence.

*Actions:*

- **PsyNetSkills:** Add a short note to experiment-implementation challenge guidance that generator-style experiments should include evidence for both generator invocation and generated experiment validation. Confidence: high. Impact: medium. Status: considering.

## Translation PO files need source occurrences for inheritance

PsyNet's translation updater did not inherit complete manual Hindi/German translations until generated `.po` entries included source occurrences such as `#: experiment.py`. Without those occurrences, `psynet translate hi de` treated the file as untranslated and attempted to call the default external translator.

*Actions:*

- **PsyNetSkills:** Add a note to the prepare-for-translation skill that manually written PO files for credential-free challenge attempts should include source occurrences matching the POT so PsyNet can inherit reviewed translations. Confidence: high. Impact: medium. Status: considering.

## Standard PsyNet test harness matters for simulation evidence

A minimal `test.py` that only imported `experiment.py` made `psynet simulate` export only trivial request/response rows. Replacing it with PsyNet's launched-experiment test harness allowed simulation to drive 12 bots through 50 trials and export 600 completed `ChoiceTrial` rows.

*Actions:*

- **PsyNetSkills:** Clarify that generated PsyNet experiments should include the standard `pytest_dallinger`/`pytest_psynet` launched-experiment test harness before simulation evidence is collected. Confidence: high. Impact: high. Status: considering.
