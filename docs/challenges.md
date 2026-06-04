# Challenges

Challenges live in `challenges/` and define tasks for agents to attempt.

Each challenge folder contains:

```text
TITLE
TYPE
INSTRUCTIONS.md
CRITERIA.md
references/
attempts/
```

`INSTRUCTIONS.md` is visible to agents and must include a `difficulty:` field.
`CRITERIA.md` is hidden from agents and used during evaluation.

## Attempt folders

Attempts live under `challenges/<challenge>/attempts/<timestamp>/`.

Each attempt should contain:

```text
challenge/
agent.json
code/
evidence/
EVALUATION.md
```

The `challenge/` directory snapshots the challenge at the time of the attempt.
The `code/` directory contains the generated implementation. The `evidence/`
directory contains material used to judge success, such as recordings, data
exports, or analysis outputs.

## Evaluation

Evaluations should include a `score:` field on a 1 to 10 scale. The dashboard
uses this field to show progress over time.

Keep written feedback specific and actionable. Strong evaluations explain both
what failed and which future skill change might prevent the same failure.
