---
name: plan-experiment
description: Collaboratively fill the shared experiment plan scaffold (Science, Design, Implementation oversight) with a human researcher before any implementation begins. Use when a user brings a new experiment idea, asks to plan or design an experiment, or needs to document an existing design before coding starts.
authors: [pmcharrison]
---

# Plan an experiment

Use this skill when a user brings a new experiment idea — whether vague or
detailed — before any implementation code is written. The goal is to reach
explicit, documented agreement on Science, Design, and Implementation decisions.

## Required reads

- Read `docs/experiment-plan.md` for field definitions, the gap-triage rules,
  the canonical reference workflow, and the compact template.

## Workflow

1. **Announce mode.** Tell the user you are filling the experiment plan together
   and that no implementation code will be written until the plan is agreed.

2. **Identify purpose first.** Ask or infer whether this is a demo,
   pilot, formal experiment, direct replication, or adaptation of an existing
   study. Purpose determines the required level of rigor across all three
   sections; establish it before filling any other field.

3. **Find the canonical reference.** When the purpose is to replicate or adapt
   an existing study — or when a well-known prior implementation exists — search
   for the source paper, preregistration, or established procedure. If its
   license permits redistribution, store a copy in `references/`; otherwise
   record only the citation and URL. Transcribe exact instruction wording,
   question text, response scales, timing values, and screening criteria into
   the plan. If the gap between the source procedure and what PsyNet can
   natively express is large (custom frontend, specialised hardware, large
   stimulus corpus requiring prior preparation, or complex external
   integrations), stop and consult the user: suggest compiling the experimental
   materials as a separate preparatory project before the full experiment is
   attempted.

4. **Fill Science.** Propose values for all Required science fields using the
   compact template from `docs/experiment-plan.md`. Apply gap triage throughout
   (see step 7). Raise the research question, conditions, dependent variables,
   and interpretation boundary with the user if they are underspecified; these
   are high-stakes for scientific validity.

5. **Fill Design.** Work through the standard participant journey stage by
   stage: consent → demographics or pre-experiment questionnaire → device or
   ability prescreens → task instructions → comprehension check → practice
   trials → main trials → post-experiment questionnaire or debrief → reward or
   bonus summary → completion and recruiter redirect. For each stage, propose
   whether it is included, the default behaviour, and any timing or pacing
   values. Mark omitted stages explicitly as out of scope. Raise choices about
   quality controls, response modality, feedback, and reward display that could
   affect scientific interpretation; default the rest.

6. **Fill Implementation oversight.** Identify the closest PsyNet demo,
   propose the experiment architecture (page-only, static trials, chain,
   adaptive, synchronous, AI/hybrid, or a combination), and flag any technical
   choices — scheduler design, data schema, bot path, credentials strategy —
   that could silently change the science or participant experience. Do not
   propose or write implementation code at this stage.

7. **Gap triage throughout.** For every underspecified field: evaluate whether
   the choice could silently change the scientific meaning, participant
   experience, data interpretation, or deployment safety. If yes, raise it with
   the user before proceeding. If no, set the most reasonable default, state it
   briefly, and mark it as overridable. Do not burden the user with questions
   about low-stakes details.

8. **Reach agreement.** Present the filled compact template. Confirm all
   Required and Negotiation-point fields with the user. Iterate until the user
   explicitly approves the plan.

9. **Save the plan.** Write the agreed plan as `references/PLAN.md` in the
   relevant challenge or experiment folder. If no folder exists yet, ask the
   user where to save it.

10. **Hand off.** Once the plan is saved and agreed, the agent may proceed to
    implementation using the `psynet-experiment-implementation` skill, or invite
    the user to create a challenge with the `create-challenge` skill.

## Rules

- Do not write any implementation code before the plan is agreed and saved.
- Do not advocate for a specific design choice before the user has expressed a
  preference.
- Do not leave Required fields blank; either fill them with a proposed default
  or mark them explicitly as out of scope with a reason.
- After every agreed revision during back-and-forth, update the saved
  `references/PLAN.md` to keep it in sync.
- Use the compact template from `docs/experiment-plan.md` as the output format,
  not free prose.
- Do not modify other skills when using this one.
