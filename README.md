# PsyNetSkills

## TLDR

PsyNetSkills is a workshop repository for making AI agents better at building
[PsyNet](https://gitlab.com/PsyNetDev/PsyNet) experiments. It does this by
combining reusable agent skills, realistic implementation challenges, recorded
attempts, human evaluations, and a dashboard that makes the whole learning loop
easy to inspect.

The main loop is simple:

1. Write or choose a challenge that represents a real PsyNet experiment task.
2. Ask one or more Cursor Cloud Agents to attempt it.
3. Review the generated experiment, evidence, timeline, and evaluation.
4. Turn recurring failures or useful discoveries into better skills, better
   challenges, or upstream PsyNet improvements.

This README is also the textual source for the PsyNetSkills dashboard index
page, so user-facing overview edits should start here.

The repository is maintained by Peter Harrison (pmch2@cam.ac.uk).

## Motivation

PsyNet is a Python framework for building and deploying online behavioral
experiments, especially experiments whose logic is richer than a simple survey:
adaptive psychophysics, iterated learning, network experiments, cultural
evolution, audio and image trials, bot testing, and dashboard-based monitoring.
It is powerful, but power brings surface area. A capable agent can write PsyNet
code quickly; a well-guided agent can write PsyNet code that is idiomatic,
testable, and easier for researchers to trust.

Agent skills are one way to provide that guidance. They turn hard-won local
knowledge into reusable procedures: which PsyNet demos to inspect, which APIs are
easy to misuse, which commands actually validate an experiment, and what evidence
a reviewer will need. Skills are most useful when they are refined against real
tasks rather than written once in the abstract.

That is where the PsyNetSkills challenge workflow helps. Challenges define
representative tasks; attempts show what an agent actually did; evaluations say
what worked and what failed; learnings identify changes worth making next. The
dashboard keeps those artifacts close together, making it easier to see whether
the system is improving and where the next skill or framework fix should land.

## Cursor Cloud Agents

Cursor Cloud Agents are remote coding agents that work in a repository branch,
run commands, edit files, collect evidence, push commits, and prepare pull
requests. For PsyNetSkills, they are useful because they make the workshop loop
parallel and reviewable: several agents can try the same challenge independently,
one agent can improve a skill while another implements an experiment, and each
result arrives as a normal version-controlled diff.

To get started with Cursor Cloud Agents for this workshop, you need access to
Nori Jacoby's team Cursor subscription. Once you have joined that subscription,
you can start agents from this repository and review their work through branches,
pull requests, and dashboard previews.

The version-control side matters. A good Cursor Cloud Agent task should end with:

- a branch containing the attempted implementation or documentation change;
- a pull request with a concise summary and test evidence;
- dashboard preview output when the change affects public challenge, attempt, or
  site content;
- enough committed artifacts for a human to reconstruct what happened.

## Quickstart

This quickstart assumes Cursor Cloud Agent use. The default unit of work is a
branch and pull request, not a local uncommitted edit.

### Implementing a challenge

Here "implementing a challenge" means writing a new challenge for future agents
to attempt.

Ask a Cursor Cloud Agent to create the challenge for you. Describe the intended
participant experience in prose: what participants should see, hear, or do; what
stimuli or inputs matter; what responses should be collected; and what would
make the implementation scientifically convincing. If there are evaluator-only
checks, say that they should be private criteria.

The agent should take care of the repository structure, metadata, validation,
and pull request. Review the generated challenge instructions, any private
criteria, the dashboard preview, and the validation output before merging.

### Attempting a challenge

Ask a Cursor Cloud Agent to attempt a specific challenge, for example:

> Attempt the `primary-color-rating` challenge.

Do not provide extra implementation instructions at attempt time. The point is to
test whether the current challenge and skills are sufficient. If the challenge is
underspecified, update the challenge in a separate change and then start a fresh
attempt.

The agent should handle the attempt structure, PsyNet checkout metadata, code,
evidence, timeline, learnings, and pull request. Once implementation and
first-pass evidence collection are complete, it should automatically prompt you
for an evaluation.

### Evaluating an attempt

Normally, you do not need to start evaluation as a separate task. The attempting
agent should prompt you for a score and prose feedback once implementation is
complete. After you respond, the agent should inspect the relevant attempt
materials, use copied private criteria when present, and update `EVALUATION.md`
with the score, feedback, and criterion checklist.

### Updating skills in PsyNetSkills

When an attempt reveals a recurring failure mode, ask a Cursor Cloud Agent to
update the relevant PsyNetSkills skill. Describe the lesson in prose and point to
the attempt or evaluation that motivated it. The agent should decide whether to
edit an existing skill or create a new one, keep the guidance compact and
procedural, validate the repository, and open a pull request. Then run another
attempt to see whether the change helped.

### Updating PsyNet

Sometimes the right fix is upstream in PsyNet rather than in PsyNetSkills: a
missing API example, a brittle command, unclear framework documentation, or a bug
that affects generated experiments. Ask a Cursor Cloud Agent to propose a change
to PsyNet. The agent should take care of the local PsyNet checkout, testing, and
upstream merge-request workflow.

## Local workflow (advanced users only)

Most workshop work should happen through Cursor Cloud Agents, because branches,
pull requests, previews, and evidence are part of the method. Advanced users can
also work locally in Cursor, Claude Code, or another coding agent, provided they
keep the same artifact discipline.

From the PsyNetSkills repository root:

```bash
uv sync --group dev
uv run psynetsk-validate
uv run pytest
uv run psynetsk-export-dashboard-data
hugo --source dashboard --destination ../public --cleanDestinationDir
```

For dashboard preview during local documentation work:

```bash
uv run psynetsk-export-dashboard-data
hugo server --source dashboard --bind 0.0.0.0 --port 1313
```

For experiment implementation, maintain a separate PsyNet checkout at
`~/PsyNet`. Inspect `~/PsyNet/demos/experiments/`, `~/PsyNet/demos/features/`,
and `~/PsyNet/docs/` for concrete patterns, and refresh the checkout before real
attempts:

```bash
cd ~/PsyNet
git checkout master
git pull --ff-only origin master
```

Large attempt evidence such as videos and data exports should be committed with
Git LFS. The generated `public/` dashboard output is not committed by default.

## Further resources

- [Skill specification](https://github.com/pmcharrison/PsyNetSkills/blob/main/docs/skills.md)
- [Challenge specification](https://github.com/pmcharrison/PsyNetSkills/blob/main/docs/challenges.md)
- [Attempt and evidence specification](https://github.com/pmcharrison/PsyNetSkills/blob/main/docs/attempts.md)
- [PsyNetSkills repository architecture](https://github.com/pmcharrison/PsyNetSkills/blob/main/docs/architecture.md)
- [Dashboard build and preview notes](https://github.com/pmcharrison/PsyNetSkills/blob/main/docs/dashboard.md)
- [PsyNet local reference](https://github.com/pmcharrison/PsyNetSkills/blob/main/docs/psynet-reference.md)
- [PsyNet documentation](https://psynetdev.gitlab.io/PsyNet/)
- [PsyNet source repository](https://gitlab.com/PsyNetDev/PsyNet)

## See also

- [SweetBean](https://autoresearch.github.io/sweetbean/) is a nearby project and
  useful comparator: a declarative Python language that compiles behavioral
  experiment specifications to jsPsych experiments for human participants and
  text-based experiments for synthetic participants.
