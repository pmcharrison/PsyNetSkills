---
title: "Workflow"
---

PsyNetSkills is a workshop loop for teaching agents to implement PsyNet
experiments reliably. Skills describe reusable agent procedures, challenges
define realistic implementation tasks, attempts record what happened, and
evaluations turn each attempt into the next skill improvement.

## The cycle

1. **Choose or define a challenge.** Use `challenges/` for tasks that represent
   realistic PsyNet experiment work. Each challenge should tell the agent what
   participant experience to build while keeping private evaluation criteria out
   of the public instructions.
2. **Start a cloud agent.** In Cursor, select this repository and start a Cloud
   Agent for the work. You can run multiple agents at once when you want
   independent attempts, separate skill edits, or parallel experiments.
3. **Initiate an attempt.** Ask the agent to attempt a specific challenge. The
   agent should create a timestamped attempt folder, implement the experiment,
   run the relevant checks, and collect evidence.
4. **Review and evaluate the attempt.** Inspect the generated code, participant
   evidence, timeline, and learnings. Score the attempt and write concrete
   feedback in `EVALUATION.md`.
5. **Improve the skills.** Convert recurring failures or useful discoveries into
   reusable guidance in `.cursor/skills/`. Keep challenge-specific fixes out of
   skills unless the lesson is likely to recur.
6. **Merge the branch.** Cloud agents work on branches and put their results into
   pull requests. The workshop uses a liberal merging strategy: merge when the
   work is done. If a change is risky or affects the wider codebase, ask Peter
   Harrison for review first.
7. **Repeat.** Run another attempt with the improved skills and compare the new
   result with previous evaluations.

## Creating skills

Skills live in `.cursor/skills/`. Each skill is a folder with a `SKILL.md` file
whose frontmatter name matches the folder name. Good skills are concise: they
tell agents when to use the skill, which PsyNet APIs or examples matter, which
commands validate the work, and which assumptions commonly fail.

For most new skills, ask an agent to create the folder and `SKILL.md` in the
right format. Then review whether the skill captures reusable process knowledge
rather than one-off instructions for a single challenge.

## Creating challenges

Challenges live in `challenges/`. A challenge should include public
`INSTRUCTIONS.md`, private `CRITERIA.md`, optional references, and an `attempts/`
folder. The public instructions should describe the intended participant
experience, stimuli, responses, and success checks clearly enough for an agent
to build the experiment without seeing the private criteria.

You can also ask an agent to draft a new challenge. Have it create the expected
files, keep criteria hidden from future attempting agents, and add only the
context needed for a fair implementation attempt.

## Working with Cursor Cloud Agents

Cursor Cloud Agents are the default way to do this workshop work. Start from
this repository, give the agent a focused task, and let it work on its own
branch. When it finishes implementing a skill, creating a challenge, or making
an attempt, its branch becomes a pull request with the resulting files and test
evidence.

Running several agents at once is encouraged when you want separate attempts or
different approaches. Keep each agent's task narrow enough that the pull request
is easy to inspect and merge.
