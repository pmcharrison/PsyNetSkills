---
name: plan-experiment
description: Collaboratively fill the shared experiment plan scaffold (Science, Design, Implementation oversight) with a human researcher before any implementation begins. Use when a user brings a new experiment idea, asks to plan or design an experiment, or needs to document an existing design before coding starts.
authors: [zeroada]
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

2. **Run the reference and purpose preflight.** Before drafting the full plan,
   ask the user which starting path they want:
   - search online for similar experiments, pipelines, papers, or prior
     implementations;
   - use references or materials they provide;
   - treat the idea as a novel demo or pilot with no canonical reference yet.
   Confirm the intended purpose: demo, pilot, formal experiment, direct
   replication, or adaptation of an existing study. Purpose determines the
   required level of rigor across all three sections; establish it before filling
   any other field. Do not search online before the user has agreed that search
   is wanted.

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

4. **Ask high-stakes pre-plan questions.** Before presenting the compact
   template, ask only the questions whose answers could change the scientific
   meaning, participant experience, data interpretation, or PsyNet architecture.
   Prefer a short grouped checklist over a complete draft when these decisions
   are still open. For PsyNet experiments, explicitly consider:
   - participant unit and assignment: within-participant, cross-participant,
     group, chain, network, or hybrid structure;
   - trial dependency: whether each participant contributes one node, multiple
     nodes, or a sequence of linked trials;
   - AI role: human participant, experiment assistant, evaluator, stimulus
     generator, bot participant, or implementation tool;
   - AI state: independent/stateless calls with explicit context versus a
     stateful agent or repeated model with memory;
   - media/output form: static snapshot, downloadable asset, sandboxed preview,
     or fully interactive participant-facing object;
   - response and comparison logic: ratings, rankings, pairwise choice, free
     text, edits, approvals, or rejection paths;
   - persistence and lineage: which prior nodes, prompts, model outputs, assets,
     and participant choices are shown, hidden, saved, and exported;
   - custom frontend need: whether PsyNet pages, controls, graphics, events, or
     assets can express the task before proposing bespoke JavaScript;
   - external services: mock-first behavior, credential policy, latency,
     timeout, retry, and failure handling.
   If the question concerns live AI provider availability or model choice, use
   the `verify-ai-model-usability` skill rather than duplicating its checks.

5. **Fill Science.** Propose values for all Required science fields using the
   compact template from `docs/experiment-plan.md`. Apply gap triage throughout
   (see step 8). Raise the research question, conditions, dependent variables,
   and interpretation boundary with the user if they are underspecified; these
   are high-stakes for scientific validity.

6. **Fill Design.** Work through the standard participant journey stage by
   stage: consent → demographics or pre-experiment questionnaire → device or
   ability prescreens → task instructions → comprehension check → practice
   trials → main trials → post-experiment questionnaire or debrief → reward or
   bonus summary → completion and recruiter redirect. For each stage, propose
   whether it is included, the default behaviour, and any timing or pacing
   values. Mark omitted stages explicitly as out of scope. Raise choices about
   quality controls, response modality, feedback, and reward display that could
   affect scientific interpretation; default the rest.

7. **Fill Implementation oversight.** Identify the closest PsyNet demo,
   propose the experiment architecture (page-only, static trials, chain,
   adaptive, synchronous, AI/hybrid, or a combination), and flag any technical
   choices — scheduler design, data schema, bot path, credentials strategy —
   that could silently change the science or participant experience. Do not
   propose or write implementation code at this stage.

8. **Gap triage throughout.** For every underspecified field: evaluate whether
   the choice could silently change the scientific meaning, participant
   experience, data interpretation, or deployment safety. If yes, raise it with
   the user before proceeding. If no, set the most reasonable default, state it
   briefly, and mark it as overridable. Do not burden the user with questions
   about low-stakes details.

9. **Reach agreement.** Present the filled compact template. Confirm all
   Required and Negotiation-point fields with the user. Iterate until the user
   explicitly approves the plan.

10. **Save the plan.** Write the agreed plan as `references/PLAN.md` in the
   relevant challenge or experiment folder. If no folder exists yet, ask the
   user where to save it.

11. **Hand off.** Once the plan is saved and agreed, the agent may proceed to
    implementation using the `psynet-experiment-implementation` skill, or invite
    the user to create a challenge with the `create-challenge` skill.

## Rules

- Do not write any implementation code before the plan is agreed and saved.
- Do not advocate for a specific design choice before the user has expressed a
  preference.
- Do not present a full compact template before resolving open preflight
  questions that could change the PsyNet architecture or scientific claims.
- Do not leave Required fields blank; either fill them with a proposed default
  or mark them explicitly as out of scope with a reason.
- After every agreed revision during back-and-forth, update the saved
  `references/PLAN.md` to keep it in sync.
- Use the compact template from `docs/experiment-plan.md` as the output format,
  not free prose.
- Do not modify other skills when using this one.

## Common failures

- Do not assume "chain" means one trial per participant; confirm whether the
  unit of contribution is a participant, trial, chain node, or repeated session.
- Do not let hidden AI memory become part of the experimental treatment unless
  it is explicitly planned, logged, and scientifically justified.
- Do not treat generated interactive websites as ordinary static stimuli.
  Decide how previews are sandboxed, whether scripts may run, and which rendered
  state counts as the stimulus.
- Do not skip lineage decisions in iterative tasks. The plan must state which
  prior versions are visible, selectable, inherited, and exported.
- Do not leave AI failure behavior vague. Participants need a planned path for
  model timeouts, invalid code, unsafe output, or render failures.
