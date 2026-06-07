# [PsyNetSkills](https://pmcharrison.github.io/PsyNetSkills/)

The repository is maintained by Peter Harrison (pmch2@cam.ac.uk),
feel free to ask him questions by email or on Slack.

## Introduction

The PsyNetSkills repository represents an ongoing initiative to make
AI agents better at building [PsyNet](https://gitlab.com/PsyNetDev/PsyNet) experiments.
The repository contains an expanding collection of
[agent skills](https://pmcharrison.github.io/PsyNetSkills/skills/),
[challenges](https://pmcharrison.github.io/PsyNetSkills/challenges/) for testing those skills,
and records of past challenge attempts, all exposed through a [live dashboard](https://pmcharrison.github.io/PsyNetSkills/).

We encourage users to contribute to these resources by implementing and testing challenges
that reflect their own research areas. This will help the generalizability of future AI agents.

We propose the following workflow:

1. Write or choose a challenge that represents a real PsyNet experiment task.
2. Instruct an agent to attempt this challenge.
3. Review the results and identify any weaknesses in the implementation process.
4. Propose corresponding adjustments/additions to the agent skills and/or to PsyNet itself.
5. Repeat from Step 1.

## Background

### PsyNet and agent skills

PsyNet is a Python framework; you can see its source code on [GitLab](https://gitlab.com/PsyNetDev/PsyNet/).
It is very flexible, and supports a diverse range of complex of experiment designs, 
such as adaptive psychophysics, iterated learning, network experiments, cultural
evolution, and multimedia experiments.
However, PsyNet has always had a pretty steep learning curve, as you have to learn about lots of new concepts
before you are ready to implement experiments.

Current frontier agents (e.g. ChatGPT 5.x, Claude Opus) are already pretty good at working with PsyNet. 
They automatically process PsyNet's documentation,
demos, and source code to get a good feel for how experiment design works. 
However, the agents lack real-world experience using PsyNet, and consequently
make various mistakes that need to be corrected before the experiment can be used for real.

Agent skills provide an approach for guiding these agents to perform these tasks better.
Each agent skill is, at its core, a simple markdown file that provides instructions about 
how to perform a given task, for example implementing a particular kind of experiment paradigm.
In the first instance, we will focus our skill development on experiment implementation,
but long-term we want our skills to cover experiment deployment too.

### Cursor Cloud Agents

Most programmers nowadays have at least some experience with agentic software development,
where one delivers instructions to an agent via a chat-message interface, and the agent 
carries out software development tasks on behalf of the user.
Cursor is a popular software solution for agentic software development, which integrates
under-the-hood with prominent LLM providers like OpenAI and Anthropic.

One way to use Cursor is as a traditional IDE, installed on one's local machine, 
and running code in a local environment.
However, we strongly encourage collaborators to try Cursor Cloud Agents for this project.
Cursor Cloud Agents can be spun up via Cursor's [web interface](https://cursor.com/agents),
or (if you prefer) from a local IDE installation.
Each Cloud Agent operates on a separate virtual machine that inherits a base image
with relevant dependencies preinstalled (here: PsyNet, Postgresql, Redis, ...).
From a security perspective, this is really helpful, as one does not have to worry about the agent
causing trouble on one's own computer; as a result, the agent can run for long periods without 
asking the user permission to perform system tasks.
From a workflow perspective, the crucial further implication is that many Cloud Agents can be 
created in parallel, which allows users to work on many problems simultaneously.

Cursor Cloud Agents are closely linked to Git workflows. When a Cloud Agent generates outputs,
it puts those outputs in a pull request on GitHub; this pull request is updated whenever you 
request changes from the agent. This pull request can then undergo code review (where someone looks
at the code to decide whether it's ok to merge), and then if everyone's happy it can be merged 
into the main codebase. If you are not familiar with these key terms (pull request, code review, merging),
please do a bit of online research into Git basics before starting your own contributions.

In this repository, the Cloud Agents are encouraged to create pull requests either to 
PsyNetSkills or to PsyNet. Pull requests to PsyNetSkills may contribute challenges or skills;
they can also contribute artifacts produced by a given challenge attempt.
Pull requests to PsyNet meanwhile contribute changes to the PsyNet source code itself.

If you just want to make a small textual change to a given skill or challenge,
you don't need to go through a Cloud Agent, however. You can just click on the 'Edit in GitHub' button
on the corresponding website page, and this will give you a simple interface for contributing 
changes to that file.

We assume that collaborators on this project will be part of Nori Jacoby's
Cursor team. This should enable you to create Cloud Agents for this repository
via the online [agents page](https://cursor.com/agents). If you have problems with this, please let us know.

An important question is which LLM you should configure the Cloud Agent to use.
In general, my experience is that a lot of pain can be saved by defaulting to top-tier models.
However, it is worthwhile also to see if we can get PsyNet performing well with cheaper agents,
so please feel free to attempt challenges using such agents.
Just be wary of making substantial code changes with cheap models. A good strategy could be to complete 
the challenge attempt with a cheap model, merge the results, then start a fresh cloud agent with a 
top-tier model to review and implement the action points proposed by the cheap model.

## Quickstart

The guide below is written assuming Cursor Cloud Agent use;
more advanced users are welcome to customize these steps to a local workflow instead.

### Implementing a challenge

Here "implementing a challenge" means writing a new challenge for future agents
to attempt.

In most cases, the idea here is that your challenge should correspond to a request
you can imagine a real user wanting to ask the agent. In the early days of this project,
we are focusing primarily on experiment implementation challenges.
So, your challenge might contain a request to implement a particular kind of experiment,
explaining the general order of events, the nature of the stimuli, the response options, and so on.

It is also possible to specify some hidden evaluation criteria. These will not be shared with the 
agent, but they will be reviewed at evaluation time. This is a good place to describe certain 
pitfalls that you want to make sure the model doesn't hit.

You can browse existing challenges on the
[Challenges page](https://pmcharrison.github.io/PsyNetSkills/challenges/). The
detailed challenge format is documented in the
[challenge specification](https://github.com/pmcharrison/PsyNetSkills/blob/main/docs/challenges.md).

### Attempting a challenge

Ask a Cursor Cloud Agent to attempt a specific challenge, for example:

> Attempt the `primary-color-rating` challenge.

Do not provide extra implementation instructions at attempt time. The point is to
test whether the current challenge and skills are sufficient. If the challenge is
underspecified, update the challenge in a separate change and then start a fresh
attempt.

The agent will proceed to carry out the task, and produce various pieces of evidence
for you to review (see 
[attempt specification](https://github.com/pmcharrison/PsyNetSkills/blob/main/docs/attempts.md)).

### Evaluating an attempt

Once the agent has completed its attempt, it should prompt you to review the generated evidence
via the dashboard (it should print you a link to visit).
This evidence should include things like code, videos, performance tests, and so on.
The agent will store your verdict in `EVALUATION.md`.

### Learning notes

After the evaluation, the agent should also initialize a collection of 'learning notes' in 
`LEARNING.md`, which include a set of concrete action points for how to improve PsyNetSkills and PsyNet.
These will need review from you, and possibly from other collaborators.
Action points each have a 'status' attribute, taking values from 
`considering`, `planned`, `in_progress`, `completed`, `dismissed`, or `superseded`.
The agent can help you keep these up to date.

### Updating skills

One possible action is to update skills in PsyNetSkills. The agent can help you draft new skills
or edit existing ones, and these can be contributed as part of your attempt pull request.
You should exercise manual review here; be warned that LLMs often generate overly verbose skills.

You can browse existing skills on the
[Skills page](https://pmcharrison.github.io/PsyNetSkills/skills/). The detailed
skill format is documented in the
[skill specification](https://github.com/pmcharrison/PsyNetSkills/blob/main/docs/skills.md).

### Updating PsyNet

Another possible action (possibly complementary to the skills contribution)
is to contribute a change to PsyNet. The agent can again help you with this;
it should take responsibility for managing the Git workflow as well as testing.

### Finishing up

Once you've finished your challenge attempt and corresponding skill contributions,
you will want to merge your contribution to the main repository branch.
First you will want to take your pull request out of Draft status.
You then should review the changes made in the pull request, using either the Cursor diff interface
or the GitHub changes interface. Try and be critical here, especially of changes to agent skills,
as these could affect lots of people.
During the June 2026 workshop we are thinking that we won't require external code review for pull requests, 
given the different time zones at play.
However, this makes it doubly critical to be self-critical about one's code. 
A good strategy is to ask the agent to review your pull request before merging it.

If someone has been working on similar parts of the codebase to you, you might encounter merge conflicts.
Don't panic! Normally the agent can solve this for you if you ask nicely.

Once you've successfully merged, you can start the workflow again from the first step
with a fresh Cloud Agent! While in theory you could reuse your pre-existing one,
it's normally good to start a fresh one to keep the context clean.

## Local workflow (advanced users only)

The workflow above can be straightforwardly customized for local development if needed.
Here are some useful commands.

To build the website locally:

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

You should maintain a PsyNet checkout at `~/PsyNet`. Make sure you are always
on an up-to-date version of the master branch:

```bash
cd ~/PsyNet
git checkout master
git pull --ff-only origin master
```

Note that large attempt evidence such as videos and data exports should be committed with Git LFS.

## Further resources

- [Skill specification](https://github.com/pmcharrison/PsyNetSkills/blob/main/docs/skills.md)
- [Challenge specification](https://github.com/pmcharrison/PsyNetSkills/blob/main/docs/challenges.md)
- [Attempt and evidence specification](https://github.com/pmcharrison/PsyNetSkills/blob/main/docs/attempts.md)
- [PsyNetSkills repository architecture](https://github.com/pmcharrison/PsyNetSkills/blob/main/docs/architecture.md)
- [Dashboard build and preview notes](https://github.com/pmcharrison/PsyNetSkills/blob/main/docs/dashboard.md)
- [PsyNet local reference](https://github.com/pmcharrison/PsyNetSkills/blob/main/docs/psynet-reference.md)
- [PsyNet documentation](https://psynetdev.gitlab.io/PsyNet/)
- [PsyNet source repository](https://gitlab.com/PsyNetDev/PsyNet)
