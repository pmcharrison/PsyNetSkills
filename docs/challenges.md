# Challenges

Challenges live in `challenges/` and define tasks for agents to attempt.

In the normal workflow, users should ask a Cursor Cloud Agent to create a
challenge from prose. The prose should describe the participant experience,
stimuli, responses, constraints, and any evaluator-only checks; the agent should
use the `create-challenge` skill and take care of the repository structure. The
details below are the specification that the agent and advanced manual
contributors should follow.

Each challenge folder contains at minimum:

```text
INSTRUCTIONS.md
attempts/
```

`INSTRUCTIONS.md` is visible to agents and must include YAML frontmatter with
the challenge title, type, and difficulty:

```markdown
---
title: Primary color rating experiment
type: experiment implementation
difficulty: 2
authors: [pmcharrison]
---
```

`authors` must list one or more GitHub author keys from `authors.yaml`; see
`docs/authors.md` for the registration workflow.

Challenges may also include `CRITERIA.md` for evaluator-facing success
criteria and `references/` for supporting material. `CRITERIA.md` is optional:
when present, agents should not read it before implementing the challenge, but
it should be used during conversational evaluation.

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

Each new attempt should initialize `LEARNINGS.md` alongside `agent.json`,
`code/`, `evidence/`, and `EVALUATION.md`. Agents use this file throughout the
attempt to record implementation findings and confidence-labelled actions
targeting PsyNetSkills or PsyNet, then revise it after evaluation when feedback
changes the lessons.
