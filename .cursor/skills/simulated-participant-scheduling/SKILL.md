---
name: simulated-participant-scheduling
description: Schedules PsyNet test participants across simulated profiles or human-AI proportions. Use when testing experiments that need a target participant distribution, bot profile mix, live human-AI scheduling, or when turn-pure-experiment-to-ai-hybrid needs participant scheduling validation.
authors: [zeroada]
---

# Overview

This skill is used to schedule participants with different profiles, or to
schedule human and AI participants with desired proportions in a test.

This skill can be used by `turn-pure-experiment-to-ai-hybrid` when live
human-AI scheduling needs implementation, testing, monitoring, or reporting.

# Workflow

The user will specify the total number of participants and the desired
participant distribution.

Check bot response functions and experiment code to see whether the desired
participant profiles are already implemented. If not, read
`psynet-simulated-participants/SKILL.md` and implement the desired participant
profiles.

Make sure each participant's profile or behavior type is recorded in experiment
data, for example in trial `vars`, participant `vars`, or another
export-visible field for future data analysis.

Then write or configure the scheduling algorithm so participants are assigned
according to the desired distribution. Launch a test, monitor the test process,
and report the actual participant distribution. Identify any issues with the
scheduling algorithm and improve it.

Once the test is completed and the data is collected, report the actual
participant distribution and the desired distribution in a markdown document.
The document should contain the participant profile description, the target
participant distribution, and the actual participant distribution.

## Scheduling algorithm and its corresponding testing

There are two scheduling situations. Think about which one applies before
implementing the scheduling algorithm and testing.

### 1. Bot test scheduling

Use case: assign 10 bots to 5/5 profiles.

Usually deterministic or seedable. Used for coverage, for example 5 random bots
and 5 normal bots.

Write an `initialize_bot` function under the `Experiment` class, or use the
experiment's simulation setup, to assign bot profiles for test fixtures.

Testing: tests assert realized distribution using simulation or exported
experiment data.

### 2. Live scheduling

Use case: live scheduling with desired participant distribution, especially to
match a human-AI ratio in real time.

Dynamic and incremental. Repeatedly checks current human count, AI count, total
count, failures, and remaining trial capacity.

Launch only enough AI bots to restore target proportions. The scheduler needs
idempotency, locking, and stop conditions.

Write a scheduler function under the `Exp` class to monitor human and AI
participant status. Note the parallel capability of the system, and add a
cutoff for running bots to keep the system stable, for example by limiting
`working` bots under a configured maximum.

Testing: test by operating a browser as participants to simulate the real-time
scheduling process. The human participant simulation must operate exactly like a
real human participant: enter through the normal recruitment or start route,
read pages, click buttons, wait through timers, answer trials, trigger
validations, and complete the experiment through the same participant-facing UI.
Do not shortcut database state, call backend endpoints directly, or use
bot-only paths for the human side of a live scheduling test.

For example, a human participant can be a browser worker, and an AI participant
can be a bot worker, to simulate human-AI hybrid scheduling.

Note: By default, the scheduling algorithm assigns the proportion at the
participant level. If the user requests scheduling participants over chains or
trials with a specific distribution or order, adjust the scheduling algorithm to
support this.

## Reporting

Monitor the process and the final distribution. Produce a markdown report with
the participant profile description, the target participant distribution, and
the actual participant distribution in the experiment. If the experiment has
substructures, such as chains or trials, summarize the distribution over the
substructures as well.

Also generate an HTML monitor dashboard from the run data. Match the running
experiment monitor as closely as practical: preserve the experiment's relevant
graph entities, such as participants, trial nodes, chains, and trials, rather
than replacing them with a generic profile summary. Color graph elements by the
participant profile, user model, or controller identity (`human`, `AI`, `bot`,
or another profile label), and include a visible legend.

Make the dashboard useful for review. Include formatted summary statistics,
filters or grouping notes, a sidebar, graph details, and expandable summaries.
When a reviewer clicks a participant, node, chain, or trial, show the important
exported information for that element, such as participant ID, controller or
profile, trial/node IDs, target/stimulus, response, status, failure state, and
finalization state. Build the HTML directly from the exported data for the run;
do not depend on a static monitor-dashboard template file.

Do not claim simulated participant behavior is real human behavior. Label bot,
AI, mock, and fixture behavior clearly.
