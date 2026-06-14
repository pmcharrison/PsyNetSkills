# Learnings

## Generator challenges need explicit generated-output evidence

This challenge asks the agent to implement a generator that consumes a Python config and emits a runnable PsyNet experiment. The standard experiment evidence checklist still applies, but the attempt plan must also demonstrate that the generator itself was invoked from the example config and that the generated experiment, not a hand-written bypass, produced the participant-flow evidence.

*Actions:*

- **PsyNetSkills:** Add a short note to experiment-implementation challenge guidance that generator-style experiments should include evidence for both generator invocation and generated experiment validation. Confidence: high. Impact: medium. Status: considering.
