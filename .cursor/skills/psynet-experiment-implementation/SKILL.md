---
name: psynet-experiment-implementation
description: Implement PsyNet experiments from text specifications, using local PsyNet source code, demos, setup commands, and validation practices.
authors: [pmcharrison]
---

# Implement PsyNet experiments

Use this skill when implementing a PsyNet experiment from a natural-language
specification.

## Steps

### Planning

The planning phase is responsible for turning the original natural-language specification into a detailed implementation plan.
The plan should be saved in PLAN.md, and have the following sections:

#### Science (optional)

Decide whether to include this based on the prompt.
The section is most relevant if the prompt is asking specifically about
research questions, hypotheses, and the like.

#### Methods

This section should look something like methods sections in a scientific paper.
It should describe the experiment, including:

- Design: includes conditions, variables, randomizations.
- Materials: includes stimuli, questionnaires, etc.
- Procedures: includes participant workflow, trial structure, stimulus presentation, response collection.

Format in academic prose.

#### Implementation

This section focuses on the software implementation of the experiment, including:

- What PsyNet constructs to use (trials, trial makers, modules, etc.)
- The general shape of the timeline
- The strategy for generating the stimuli
- Any external dependencies

### Human review

Once the plan is complete, ask the human user to review it and provide feedback.
Only continue when they are happy.

### Developing the experiment

Use the develop-experiment-code skill to implement the experiment.

### Run simulations

Use `psynet simulate` to simulate participants and produce an example dataset.
This dataset should contain a decent number of participants representative of a real study.

### Develop analysis scripts

Write scripts to analyze the generated data.
Use Jupyter notebooks for this.
These notebooks should include inferential statistics and plots,
designed to address relevant research questions.
If the implementation is inspired by a published paper, replicate the analyses reported in the paper as closely as possible.

### Review

Review the outcomes of the previous steps and identify any serious issues that need to be addressed.
Return to previous steps if necessary to address these.

### Final report

Compile a final report of the experiment (REPORT.md), summarizing the process taken
and any findings that arose.