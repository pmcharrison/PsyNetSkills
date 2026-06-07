# PsyNetSkills

## TLDR

PsyNetSkills is a workshop repository for making AI agents better at building
[PsyNet](https://gitlab.com/PsyNetDev/PsyNet) experiments. It does this by
combining reusable agent skills, realistic implementation challenges, recorded
attempts, human evaluations, and a dashboard that makes the whole learning loop
easy to inspect.

The main loop is simple:

1. Write or choose a challenge that represents a real PsyNet experiment task.
2. Ask one or more Cloud Agents to attempt it.
3. Review the generated experiment, evidence, timeline, and evaluation.
4. Turn recurring failures or useful discoveries into better skills, better
   challenges, or upstream PsyNet improvements.

This README is also the textual source for the PsyNetSkills dashboard index
page, so user-facing overview edits should start here.

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

## Cloud Agents

Cloud Agents are remote coding agents that work in a repository branch, run
commands, edit files, collect evidence, push commits, and prepare pull requests.
For PsyNetSkills, they are useful because they make the workshop loop parallel
and reviewable: several agents can try the same challenge independently, one
agent can improve a skill while another implements an experiment, and each result
arrives as a normal version-controlled diff.

The version-control side matters. A good Cloud Agent task should end with:

- a branch containing the attempted implementation or documentation change;
- a pull request with a concise summary and test evidence;
- dashboard preview output when the change affects public challenge, attempt, or
  site content;
- enough committed artifacts for a human to reconstruct what happened.

## Quickstart

This quickstart assumes Cloud Agent use. The default unit of work is a branch
and pull request, not a local uncommitted edit.

### Implementing a challenge

Here "implementing a challenge" means writing a new challenge for future agents
to attempt.

1. Ask a Cloud Agent to create a new challenge under `challenges/<slug>/`.
2. Put the public task in `INSTRUCTIONS.md`: participant experience, stimuli,
   responses, scientific checks, and any constraints that matter.
3. Put private evaluator guidance in `CRITERIA.md` when you need hidden success
   criteria. Attempting agents should not read this file before evidence
   collection is complete.
4. Keep challenge-specific reference material in `references/`.
5. Review the pull request, dashboard preview, and validation output before
   merging.

### Attempting a challenge

Ask a Cloud Agent to attempt a specific challenge, for example:

> Attempt the `primary-color-rating` challenge. Use the available PsyNetSkills
> skills, implement the experiment, run the relevant checks, and collect
> participant-facing evidence.

For real experiment attempts, the agent should refresh its local PsyNet checkout
before implementation and record the checkout in `agent.json`. Attempts should
include code, evidence, a timeline, learnings, and enough test output for a
reviewer to judge the result.

### Evaluating an attempt

Review the pull request and dashboard attempt page. Inspect the generated code,
participant video, performance evidence, exported data, timeline, and learning
notes. If `CRITERIA.md` exists, use the copied criteria in the attempt snapshot
for evaluation. Then ask the agent to update `EVALUATION.md` with a score,
specific feedback, and any criterion checklist that belongs in the record.

### Updating skills in PsyNetSkills

When an attempt reveals a recurring failure mode, update the relevant skill in
`.cursor/skills/`. Good skill changes are compact and procedural: they tell
future agents what to inspect, what command to run, what evidence to collect, or
which PsyNet assumption to avoid. Commit the skill change through the same
branch-and-PR workflow, then run another attempt to see whether it helped.

### Updating PsyNet

Sometimes the right fix is upstream in PsyNet rather than in PsyNetSkills: a
missing API example, a brittle command, unclear framework documentation, or a bug
that affects generated experiments. In that case, use the local `~/PsyNet`
checkout, make the PsyNet change on its own branch, run PsyNet's tests or demo
checks, and prepare an upstream merge request. Keep production credentials out of
PsyNetSkills attempts and out of evidence artifacts.

## Local workflow (advanced users only)

Most workshop work should happen through Cloud Agents, because branches, pull
requests, previews, and evidence are part of the method. Advanced users can also
work locally in Cursor, Claude Code, or another coding agent, provided they keep
the same artifact discipline.

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

- [Skill specification](docs/skills.md)
- [Challenge specification](docs/challenges.md)
- [Attempt and evidence specification](docs/attempts.md)
- [PsyNetSkills repository architecture](docs/architecture.md)
- [Dashboard build and preview notes](docs/dashboard.md)
- [PsyNet local reference](docs/psynet-reference.md)
- [PsyNet documentation](https://psynetdev.gitlab.io/PsyNet/)
- [PsyNet source repository](https://gitlab.com/PsyNetDev/PsyNet)

## See also

- [SweetBean](https://autoresearch.github.io/sweetbean/) is a nearby project and
  useful comparator: a declarative Python language that compiles behavioral
  experiment specifications to jsPsych experiments for human participants and
  text-based experiments for synthetic participants.
