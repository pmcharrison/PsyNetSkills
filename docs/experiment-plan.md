# Shared experiment plan

This document proposes a planning scaffold for PsyNet experiments that a human
researcher and an agent can share before implementation. It is meant to sit
between a prose idea and a challenge or experiment build: detailed enough to
remove ambiguity, but not so implementation-heavy that it replaces PsyNet skills
or code review.

The structure is based on the current PsyNetSkills challenge set, the attempt
schema documented in this repository, and recurring patterns in the local PsyNet
checkout (`~/PsyNet/demos/experiments/`, `~/PsyNet/demos/features/`, and
`~/PsyNet/docs/`). At the time of writing, the repository checkout contains
challenge definitions and attempt templates/specifications, but no committed
completed attempt directories under `challenges/*/attempts/`; attempt insights
therefore come from `docs/attempts.md`, validation/dashboard tests, and skill
templates rather than from completed attempt artifacts.

## How to use this plan

Create one plan for each experiment before an agent starts coding. The human
should fill or approve the scientific and design decisions; the agent can propose
defaults, identify PsyNet demos that match the design, and flag contradictions.
Implementation entries are not a line-by-line coding recipe. They are the places
where human oversight is valuable because a wrong technical choice can change the
scientific task, participant experience, deployment safety, or data interpretation.

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
class names.

### Required fields

- **Participant journey**: ordered flow from consent or welcome through
  instructions, practice, main trials, feedback, debrief, and completion.
- **Trial experience**: what participants see or hear on each trial, what action
  they take, whether feedback appears, and how progress is communicated.
- **Response modality**: buttons, keyboard, sliders, text, audio/video recording,
  drawing, chat, synchronous interaction, or another input mode.
- **Timing**: display durations, response windows, deliberation windows,
  playback rules, timeouts, and whether participants can replay stimuli.
- **Assignment and counterbalancing**: randomization, block order, repeated
  stimuli, between-participant condition assignment, group assignment, and role
  assignment.
- **Quality controls**: comprehension checks, attention checks, volume
  calibration, headphone screening, practice accuracy, device constraints, and
  failure paths.
- **Feedback and scoring visible to participants**: what participants learn about
  correctness, payoff, progress, or group outcomes.
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

- Required: research question:
- Required: construct:
- Required: hypotheses or expected patterns:
- Required: conditions / independent variables:
- Required: dependent variables:
- Required: stimulus domain and source:
- Required: participant population:
- Required: interpretation boundary:
- Required: minimal analysis:
- Optional: sample-size rationale:
- Optional: adaptive / group / AI logic:
- Optional: ethical or domain constraints:
- Negotiation points:
- Out of scope:

## Design

- Required: participant journey:
- Required: trial experience:
- Required: response modality:
- Required: timing and replay rules:
- Required: assignment and counterbalancing:
- Required: quality controls:
- Required: participant-visible feedback/scoring:
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
