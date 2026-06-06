# Challenges

Challenges live in `challenges/` and define tasks for agents to attempt.

Each challenge folder contains:

```text
INSTRUCTIONS.md
CRITERIA.md
references/
attempts/
```

`INSTRUCTIONS.md` is visible to agents and must include YAML frontmatter with
the challenge title, type, and difficulty:

```markdown
---
title: Primary color rating experiment
type: experiment implementation
difficulty: 2
---
```

`CRITERIA.md` is hidden from agents and used during evaluation.

## Challenge instructions

`INSTRUCTIONS.md` should state the task in ordinary language, with enough detail
for an agent to implement the experiment without reading hidden evaluation
criteria. Keep the prompt focused on the intended behavior rather than the exact
implementation strategy unless a specific PsyNet API is part of the challenge.

For experiment implementation challenges, the instructions should normally
describe the participant experience, the stimuli or inputs, the responses to
collect, and any scientific checks that matter for success.

Attempts and evaluations are documented separately in the Attempts section.

## Attempt learning notes

Each new attempt should include `LEARNINGS.md` alongside `agent.json`,
`code/`, `evidence/`, and `EVALUATION.md`. Agents use this file to record
implementation findings and suggestions for improving PsyNetSkills, PsyNet, or
the original challenge instructions.
