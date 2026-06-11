# Shared experiment plan

This document proposes a planning scaffold for PsyNet experiments that a human
researcher and agents can share before implementation. It is meant to sit
between a prose idea and a challenge or experiment build: detailed enough to
remove ambiguity, but not so implementation-heavy that it replaces PsyNet skills
or code review.

The structure is based on the current PsyNetSkills challenge set, the attempt
schema documented in this repository, and recurring patterns in the local PsyNet
checkout (`~/PsyNet/demos/experiments/`, `~/PsyNet/demos/features/`, and
`~/PsyNet/docs/`).

## How to use this plan

Create one plan for each experiment before an agent starts coding. The human
should fill or approve the scientific, design, and implementation decisions; the agent can propose
defaults, identify PsyNet demos that match the design, and flag contradictions.
Implementation entries are not a line-by-line coding recipe. They are the places
where human oversight is valuable because a wrong technical choice can change the
scientific task, participant experience, deployment safety, or data interpretation.

**Canonical reference.** Before filling the template, identify a published
paper, preregistration, or established procedure that describes the intended
paradigm. If its license permits redistribution, store a copy (PDF or HTML) in
the `references/` directory of the relevant challenge or experiment folder;
otherwise record only the citation and a URL. Transcribe the key procedure
into the Science and Design sections of the plan — exact instruction wording,
question text, response scales, timing values, and screening criteria from the
original study. If the gap between the source procedure and what PsyNet can
natively express is large (custom frontend, specialised hardware, a large
stimulus corpus requiring prior preparation, or complex external integrations),
stop before filling the Implementation section and consult the user: suggest
compiling the experimental materials as a separate preparatory project first.

Before proposing defaults, agents should work through the plan systematically
and identify any logical gaps, contradictions, or underspecified fields. For
each gap, evaluate whether it requires human judgment: if the choice could
silently change the scientific meaning, participant experience, data
interpretation, or deployment safety, raise it explicitly with the human before
proceeding. If the gap is low-stakes or has an obvious reasonable default,
set that default, state it briefly, and mark it as overridable — do not burden
the human with questions about minor details. Agents should not advocate for a
specific design choice before the human has expressed a preference.

Use these labels:

- **Required**: must be decided before implementation.
- **Optional**: fill when relevant to the paradigm.
- **Negotiation point**: should be discussed if uncertain, risky, or likely to
  change the scientific interpretation.
- **Out of scope**: explicitly excluded from the current build.

## Part 1: Science

The science section states what the experiment is meant to learn and what it is
not allowed to claim.

### Required fields

- **Canonical reference**: the primary published paper, preregistration, or
  established procedure this experiment is based on or replicates, if one
  exists. Record the citation and either the `references/` path (if stored
  locally) or a URL. Note which sections of the plan were transcribed directly
  from this source. If no canonical reference exists, state that explicitly.
- **Research question**: the primary question in ordinary language.
- **Scientific construct**: the psychological, behavioral, cultural, perceptual,
  social, or interaction process being measured.
- **Hypotheses or expected patterns**: directional predictions, exploratory
  goals, or a statement that the study is a technical demonstration.
- **Conditions and independent variables**: condition names, manipulation levels,
  within- or between-participant structure, and whether labels are visible to
  participants or internal only.
- **Dependent variables**: response values, reaction times, recordings,
  interaction logs, choices, ratings, free text, or derived scores.
- **Stimulus domain**: what stimuli are, where they come from, how many are used,
  and why this set is sufficient for the current study stage.
- **Participant population**: intended population, inclusion/exclusion criteria,
  platform, and whether bots or simulations are only for local validation.
- **Data interpretation boundary**: which claims are valid from local bots,
  simulations, pilots, or production participants, and which claims are not.
- **Minimal analysis**: participant count, trial count, exclusions, condition
  summaries, planned figures/tables, and the report or export expected after a
  run.
- **Purpose**: whether this is a proof-of-concept demo, a pilot, a formal
  experiment, a direct replication, or an adaptation of an existing study. The
  intended purpose sets the level of rigor expected across all three plan
  sections: the depth of scientific justification, the fidelity of the
  participant-facing design, and the completeness of implementation and
  evidence collection.

### Optional fields

- **Power or sample-size rationale**: target precision, practical pilot size, or
  production recruitment target.
- **Adaptive or sequential logic**: how later stimuli depend on earlier
  responses, stopping rules, and what counts as valid adaptation.
- **Social or group dynamics**: group size, matching logic, roles, information
  sharing, payoff coupling, and dropout assumptions.
- **AI or hybrid participants**: model role, prompt parity with human
  instructions, allowed information, target human/AI proportions, and whether AI
  data is analyzed separately.
- **Ethical or domain constraints**: sensitive stimuli, deception, consent
  language, debriefing, data minimization, and external approvals.

### Science clarification prompts

- Is this a production study, a pilot, a teaching demo, or a pipeline proof?
- Which scientific result would make the study successful?
- Which simplifications are acceptable for the demo version?
- What should reviewers avoid over-interpreting?
- What data field would be most damaging to omit?

## Part 2: Design

The design section describes the participant-facing experience and assignment
logic in result-oriented terms. It should be readable without knowing PsyNet
class names. The required level of detail scales with the purpose declared in
Part 1: a formal experiment should specify every stage and parameter; a pilot
may leave lower-stakes fields at sensible defaults, which the agent should
document explicitly rather than leave blank.

### Required fields

- **Participant journey**: the complete ordered sequence from arrival to exit.
  A standard flow for a formal experiment includes: consent → demographics or
  pre-experiment questionnaire → device or ability prescreens (audio
  calibration, headphone check, colour-vision test) → task instructions →
  comprehension check → practice trials → main trials → post-experiment
  questionnaire or debrief → reward or bonus summary shown to participant →
  completion and recruiter redirect. For a pilot, omit questionnaires,
  prescreens, and comprehension checks unless the task requires them, and
  apply defaults for debrief and reward display. Mark any omitted stage
  explicitly as out of scope rather than leaving it blank.
- **Trial experience**: what participants see or hear on each trial, what action
  they take, whether feedback appears, and how progress is communicated.
- **Response modality**: buttons, keyboard, sliders, text, audio/video recording,
  drawing, chat, synchronous interaction, or another input mode.
- **Timing and pacing**: per-trial display durations, response windows,
  deliberation windows, playback rules, timeouts, whether participants can
  replay stimuli, and whether a progress bar or trial counter is shown. No
  experiment-wide time limit is assumed unless stated. For formal experiments,
  specify every value; for pilots, document which values are defaults and which
  were measured or drawn from the canonical reference.
- **Assignment and counterbalancing**: randomization, block order, repeated
  stimuli, between-participant condition assignment, group assignment, and role
  assignment.
- **Quality controls**: comprehension checks, attention checks, volume
  calibration, headphone screening, practice accuracy, device constraints, and
  failure paths.
- **Feedback and scoring visible to participants**: what participants learn
  about correctness, payoff, progress, or group outcomes — including whether
  accumulated reward or bonus is shown trial-by-trial, at the end of the
  session, or not at all, and how the final reward calculation is explained
  before participants exit.
- **Completion states**: success, rejection, consent rejection, timeout,
  technical failure, and participant abort behavior.

### Optional fields

- **Visual direction**: layout, branding, card style, image size, spacing,
  color/feedback conventions, and any reference mockups.
- **Audio/media direction**: calibration, playback gating, waveform or progress
  display, recording quality checks, and replacement plan for demo assets.
- **Practice or training phase**: number of practice trials, feedback, pass/fail
  threshold, and whether practice data is exported.
- **Participant evidence profile**: the canonical path to record a review video,
  the expected happy path, and edge cases that should be visible in evidence.
- **Accessibility needs**: keyboard alternatives, captions/transcripts, color
  contrast, screen size assumptions, and language/translation requirements.

### Design clarification prompts

- What must the participant understand before the first scored trial?
- Which parts of the interface are scientifically meaningful rather than
  cosmetic?
- Should trial numbers or block labels be shown, and must they match a fixed
  order?
- Are participants allowed to pause, replay, skip, or revise responses?
- What participant behavior should cause exclusion, retry, or rejection?

## Part 3: Implementation oversight

The implementation section identifies the technical choices that need human
review. The agent can scaffold these with PsyNet skills, but the human should
confirm that the chosen implementation preserves the science and design.

### Required fields

- **PsyNet version and base demo**: target PsyNet checkout, closest demo path,
  and what must remain unchanged from the base paradigm.
- **Experiment architecture**: page-only, static trials, chain/network,
  adaptive, synchronous multi-participant, AI/hybrid, deployment-operations
  workflow, or a combination.
- **Core PsyNet mapping**: intended use of timeline pages, trial classes, nodes,
  trial makers, modules, groupers, assets, recruiters, and controls.
- **Configuration strategy**: which parameters live in `config.txt`, class
  variables, manifests, environment variables, or command-line/testing fixtures.
- **Stimulus and asset pipeline**: manifest format, asset generation/download,
  licensing/source metadata, file sizes, reproducibility, and replacement of demo
  assets with production assets.
- **Data schema**: fields saved per participant, trial, node, group, recording,
  AI call, and export summary; include field names when possible.
- **Bot and simulation path**: bot responses, test participants, deterministic
  versus stochastic simulation, and parity between bot and browser submissions.
- **Testing plan**: expected `psynet test local` behavior, custom assertions,
  participant video path, performance or multi-bot checks, export checks, and
  analysis script checks.
- **Deployment plan**: local-only, SSH, Heroku, or other target; pre-deploy
  routines; external services; credentials policy; and teardown/export safety.
- **Evidence and review artifacts**: participant recording, performance JSON,
  monitor snapshot, exported data, analysis outputs, logs, and known blockers.

### Optional fields

- **Custom frontend justification**: why built-in PsyNet pages, controls,
  graphics, events, or modules are insufficient.
- **External API integration**: mock mode, live verification conditions, timeout
  and retry behavior, prompt/version logging, and secret handling.
- **Performance envelope**: expected concurrency, duration, load-test bot count,
  slow operations, and acceptable failure thresholds.
- **Data export customization**: `get_basic_data` needs, anonymization, derived
  tables, and archive contents.
- **Translation/localization plan**: participant-facing strings, locale config,
  extraction checks, and language-specific assets.
- **Operations constraints**: commands that are review-only, actions that must
  not be run by an agent, and evidence that distinguishes dry-run plans from live
  deployment actions.

### Implementation clarification prompts

- Which PsyNet demo is the closest behavioral and technical starting point?
- Which implementation choice could silently change the experiment's scientific
  meaning?
- What should happen if local services, external APIs, media devices, or
  deployment targets are unavailable?
- Which secrets or credentials are needed, and how will the local mock path avoid
  real credentials?
- Which evidence artifact will convince a reviewer that the participant-facing
  flow and saved data match the plan?

## Shared minimum checklist

Before implementation starts, the plan should answer these questions:

1. What is the scientific question, and what claim is explicitly out of scope?
2. What are the conditions, assignment rules, stimuli, responses, and saved data?
3. What does the participant do from start to finish?
4. What PsyNet paradigm and base demo should the agent use?
5. What quality controls, practice, feedback, and completion states are needed?
6. What fields must appear in exported data for analysis?
7. What tests and review artifacts will prove the experiment works locally?
8. What deployment, credential, or external-service actions require human review?

## Compact template

Copy this template into a challenge reference, planning issue, or experiment
README when starting a new experiment.

```markdown
# Experiment plan: <title>

## Science

- Required: canonical reference (citation + URL or `references/` path):
- Required: research question:
- Required: construct:
- Required: hypotheses or expected patterns:
- Required: conditions / independent variables:
- Required: dependent variables:
- Required: stimulus domain and source:
- Required: participant population:
- Required: interpretation boundary:
- Required: minimal analysis:
- Required: purpose (demo / pilot / formal experiment):
- Optional: sample-size rationale:
- Optional: adaptive / group / AI logic:
- Optional: ethical or domain constraints:
- Negotiation points:
- Out of scope:

## Design

- Required: participant journey (consent → questionnaire → prescreens →
  instructions → comprehension check → practice → main trials → debrief →
  reward summary → completion; mark omitted stages as out of scope):
- Required: trial experience:
- Required: response modality:
- Required: timing, progress bar, and replay rules:
- Required: assignment and counterbalancing:
- Required: quality controls:
- Required: participant-visible feedback, scoring, and reward display:
- Required: completion states:
- Optional: visual direction:
- Optional: audio/media direction:
- Optional: practice/training:
- Optional: participant evidence profile:
- Optional: accessibility needs:
- Negotiation points:
- Out of scope:

## Implementation oversight

- Required: PsyNet version and base demo:
- Required: experiment architecture:
- Required: core PsyNet mapping:
- Required: configuration strategy:
- Required: stimulus and asset pipeline:
- Required: data schema:
- Required: bot and simulation path:
- Required: testing plan:
- Required: deployment plan:
- Required: evidence and review artifacts:
- Optional: custom frontend justification:
- Optional: external API integration:
- Optional: performance envelope:
- Optional: export customization:
- Optional: translation/localization plan:
- Optional: operations constraints:
- Negotiation points:
- Out of scope:
```

## Patterns behind the template

The current challenge set repeatedly asks agents to specify or infer stimulus
sets, response modalities, trial order, local evidence, saved data, and
deployment boundaries. PsyNet demos repeatedly organize those choices around
timelines, static or chain trials, trial makers, assets, consent/prescreens,
recruiters, bonuses, exports, and bot tests. The plan therefore separates
science, design, and implementation oversight so that human researchers can own
the scientific and participant-facing intent while agents use PsyNet-native
implementation patterns to realize it.
