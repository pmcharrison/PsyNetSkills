---
name: psynet-experiment-implementation
description: A structured, gated process for implementing PsyNet experiments. Confirms the purpose and user intention first, then plans Science, Method, and Implementation as separately reviewed sections of a human-readable PLAN.md backed by an authoritative PLAN_DETAILS.md, before any coding, simulations, analysis, and reporting.
authors: [pmcharrison]
---

# Implement PsyNet experiments

Use this skill when implementing a PsyNet experiment from a natural-language
specification or research idea.

## Modes

- **Interactive mode** (default): a user brings an idea in conversation. Run
  the staged planning gates below, pausing for explicit user confirmation at
  each gate.
- **Challenge mode**: the experiment is a PsyNetSkills challenge attempt run
  under the `attempt-challenge` skill, which forbids asking for supplementary
  instructions at attempt time. Infer the purpose and high-stakes decisions
  from `INSTRUCTIONS.md`, record each inference and the options you considered
  in the `PLAN_DETAILS.md` decision log, draft all sections in one pass, and surface
  everything at the single plan-review pause required by `attempt-challenge`.

## Planning

Planning turns the original idea or specification into two companion files,
filled **one section at a time** (Science, then Method, then Implementation).
Save both at the attempt root in challenge mode (the dashboard renders
`PLAN.md` at the attempt page's `#plan` anchor and `PLAN_DETAILS.md` as a
collapsed section at the end of the page) or in the experiment project folder
in interactive mode; if no folder exists yet, ask the user where to save
them.

- `PLAN.md`, from `assets/PLAN_TEMPLATE.md`: the human-readable plan that the
  dashboard renders. Flowing prose covering science, method, and
  implementation that a reviewer can absorb in one pass, ending with a
  pointer to the details file. No status tables, decision tables, or decision
  log here.
- `PLAN_DETAILS.md`, from `assets/PLAN_DETAILS_TEMPLATE.md`: the
  **authoritative specification**. Section status table, per-stage decision
  tables, decision log, and the exact technical plan. Implementation must
  match this file exactly; readable prose in `PLAN.md` never licenses
  deviation from it. Keep the status table current at every step so any
  reader (or a resumed agent session) can see where the workflow stands.

Core planning rules:

- Do not start drafting a section until the previous section is approved
  (interactive mode).
- Do not write any experiment code until all sections are approved.
- **Propose, don't decide.** Whenever a decision could change the scientific
  meaning, participant experience, data interpretation, or PsyNet
  architecture, present 2-3 concrete options with trade-offs and a
  recommendation, then wait for the user's choice. Batch the options for a
  stage into one message; never present a menu for something you can safely
  default. Low-stakes gaps get a reasonable default, stated briefly and marked
  overridable.
- Write `PLAN.md` in plain academic prose, scaled to the purpose: a simple
  demo needs a few paragraphs, a formal experiment proportionally more. Keep
  checklist labels (Required/Optional) and workflow scaffolding out of it;
  the coverage checklists in this skill's `references/` are for you, not the
  reader.
- Record decisions in the `PLAN_DETAILS.md` decision log **only where a real
  alternative existed or a nontrivial inference was made**: what was chosen,
  over what alternatives, why, and who approved it (or that it was a
  default). Do not log choices forced by the instructions.
- Keep the two files in sync after every agreed revision. If they conflict,
  fix the conflict at review; `PLAN_DETAILS.md` wins in the meantime.

### Stage 0: Purpose intake

Before drafting anything, confirm the purpose of the implementation, because
it configures the rest of the workflow:

| Purpose | Science section | Method section | Literature step |
|---|---|---|---|
| Simple implementation / technical demo | Skipped; recorded as out of scope in the plan | Light: defaults allowed, decision tables still required in PLAN_DETAILS.md | None |
| Replication / adaptation of an existing study | Transcribed from the source study, not invented | Fidelity-driven: deviations from the source are the negotiation points | Required: locate and verify the source |
| New science question | Full: propose 2-3 candidate framings for user choice | Full decision matrix with alternatives | Recommended: grounding and expected effect sizes |

In interactive mode, ask the user which purpose applies (with these options
described) together with any blocking ambiguities in the idea itself. In
challenge mode, infer the purpose from the challenge instructions and record
the inference in the decision log. Write the purpose at the top of `PLAN.md`.

### Stage 1: Science

Skip for simple implementations (record "out of scope" with the reason so the
plan is self-describing). Otherwise:

- Read `references/science-checklist.md` and work through it while drafting.
- For a new science question, propose 2-3 candidate framings (research
  question, construct, hypotheses, question archetype) with what each can and
  cannot claim; let the user pick or merge before writing the section.
- For a replication or adaptation, follow
  `references/literature-grounding.md` to locate and verify the source study
  and store materials under the experiment or challenge folder's
  `references/`. Transcribe the question, hypotheses, measures,
  and key procedure values from the source; the gate question becomes "did we
  faithfully capture the source study?".
- Gate: present the drafted section; iterate until approved.

### Stage 2: Method

This section should read like the Methods section of a paper (Design,
Participants, Materials, Procedure, Analysis), in prose.

- Read `references/method-checklist.md` and work through its design-decision
  matrix. The matrix items (within vs. between participants, static trials
  vs. chain/network, synchronous structure, AI involvement, prescreening,
  sample size, analysis plan) must never be skipped or silently defaulted.
- Delegate specialised decisions to their owner skills:
  `simple-round-structure` for trial/chain classification,
  `psynet-synchronous-experiments` and
  `psynet-realtime-synchronous-experiments` for synchronous designs,
  `participant-filtering-and-prescreening` for prescreens,
  `turn-pure-experiment-to-ai-hybrid` and `verify-ai-model-usability` for AI
  or hybrid participation.
- Treat the analysis plan as locked once the section is approved: later
  deviations must be recorded in the decision log, never made silently.
- Gate: present the drafted section; iterate until approved.

### Stage 3: Implementation plan

This section is technical; bullets, file paths, and PsyNet class names are
appropriate.

- Read `references/implementation-checklist.md` and
  `references/experiment-patterns.md`.
- Identify the closest PsyNet demo, the experiment architecture, the timeline
  shape, the stimulus pipeline, the data schema, and the local testing and
  evidence plan. Do not write experiment code at this stage.
- Gate: present the drafted section; iterate until approved.

### Developing the experiment

Use the `develop-experiment-code` skill to implement the experiment.

### Run simulations

Use `psynet simulate` to simulate participants and produce an example dataset.
This dataset should contain a decent number of participants representative of
a real study.

### Develop analysis scripts

Write scripts to analyze the generated data. Use Jupyter notebooks for this.
These notebooks should include inferential statistics and plots, designed to
address relevant research questions. Follow the analysis plan approved in the
Method section; if the implementation is inspired by a published paper,
replicate the analyses reported in the paper as closely as possible. Log any
deviation from the approved analysis plan in the `PLAN_DETAILS.md` decision
log.

### Review

Review the outcomes of the previous steps and identify any serious issues that
need to be addressed. Use `references/validation.md` for functional and
performance checks. Return to previous steps if necessary.

### Final report

Compile a final report of the experiment (REPORT.md), summarizing the process
taken and any findings that arose.

## Common failures

- Do not decide unilaterally whether the science section is needed; that is
  what the purpose intake is for.
- Do not assume "chain" means one trial per participant; confirm whether the
  unit of contribution is a participant, trial, chain node, or repeated
  session.
- Do not let hidden AI memory become part of the experimental treatment unless
  it is explicitly planned, logged, and scientifically justified.
- Do not skip lineage decisions in iterative tasks: the plan must state which
  prior versions are visible, selectable, inherited, and exported.
- Do not leave AI failure behavior vague; participants need a planned path for
  model timeouts, invalid output, or render failures.
- Do not copy the agent-facing checklist labels into the plan files; the
  document the user reviews should be plain prose.
- Do not let workflow scaffolding (status tables, decision tables, decision
  logs) leak into PLAN.md; it belongs in PLAN_DETAILS.md. Conversely, do not
  let readable prose in PLAN.md drift from the binding specification in
  PLAN_DETAILS.md.
