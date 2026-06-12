---
name: psynet-experiment-implementation
description: A structured process for implementing PsyNet experiments, including planning, simulations, analysis, and reporting.
authors: [pmcharrison]
---

# Implement PsyNet experiments

Use this skill when implementing a PsyNet experiment from a natural-language
specification.

## Blocking review gate

Before editing experiment code, write the implementation plan and stop for human
review.

1. Read the experiment specification and any required supporting skills.
2. Save the plan in `PLAN.md`.
3. Ask the human user to review the plan and provide feedback.
4. Do not edit `experiment.py`, templates, assets, tests, or other experiment
   code until the user explicitly approves the plan or asks you to proceed.

This gate overrides autonomous end-to-end implementation workflows, including
challenge-attempt workflows. Do not treat a generic instruction to "attempt" or
"implement" an experiment as approval to skip plan review.

If you use a todo list, the first implementation todo for this skill must be
`write-plan-await-review`, and it must remain in progress until the human review
gate is satisfied.

## Steps

### Planning

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
Only continue when they are happy. If another skill instructs you to keep working
autonomously, pause that workflow here and resume it only after explicit plan
approval.

### Developing the experiment

After the plan is approved, use the develop-experiment-code skill to implement
the experiment.

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