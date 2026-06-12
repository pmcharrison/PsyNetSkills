# Method section checklist (agent-facing)

Work through this checklist while drafting the Method section of PLAN.md.
Write the section itself as prose like a paper's Methods section (Design,
Participants, Materials, Procedure, Analysis); do not copy these labels into
PLAN.md.

## Design-decision matrix

These decisions must never be skipped or silently defaulted. Where a real
alternative exists, present options with trade-offs and a recommendation;
where the answer is forced by the science or the challenge instructions,
record it in the key-decisions table with a one-line justification.

- **Within vs. between participants**: which manipulations vary within a
  session and which across participants; counterbalancing and block order.
- **Trial structure**: static trials from a fixed manifest vs. explicit
  chain/network/node architecture. Use the `simple-round-structure` skill's
  classification checklist; do not guess.
- **Synchronous structure**: none / grouped-but-asynchronous / live
  synchronous interaction. Use `psynet-synchronous-experiments` and, for
  websocket interaction within one trial,
  `psynet-realtime-synchronous-experiments`.
- **AI involvement**: none / stimulus generator / evaluator / bot participant
  / hybrid human-AI. Distinguish stateless calls with explicit context from
  stateful agents with memory; hidden AI memory must never silently become
  part of the treatment. Use `turn-pure-experiment-to-ai-hybrid` and
  `verify-ai-model-usability` when AI participates.
- **Assignment and randomization**: condition assignment, stimulus sampling,
  group and role assignment.
- **Sample size and rationale**: target N with a justification — expected
  effect size from the literature, a practical pilot size, or an explicit
  statement that the run is a technical validation.
- **Prescreens and quality controls**: comprehension checks, attention
  checks, audio/headphone calibration, practice accuracy, device constraints,
  and failure paths. Use `participant-filtering-and-prescreening` when the
  task needs ability or device screening.
- **Analysis plan**: the primary statistical model (it must respect the
  design's nesting, e.g. trials within participants), primary and secondary
  outcomes, exclusion rules, and explicit decision rules for what supports or
  refutes the hypotheses. Once the Method section is approved this plan is
  locked: later deviations are logged in the decision log, never silent.

## Participant journey

Walk the standard journey stage by stage and state for each whether it is
included: consent → demographics or pre-experiment questionnaire → device or
ability prescreens → task instructions → comprehension check → practice
trials → main trials → post-experiment questionnaire or debrief → reward or
bonus summary → completion and recruiter redirect. Mark omitted stages
explicitly as out of scope rather than leaving them blank.

Also specify, in prose:

- Trial experience: what participants see or hear, what action they take,
  whether feedback appears, and how progress is communicated.
- Response modality: buttons, keyboard, sliders, text, audio/video recording,
  drawing, chat, or another input mode.
- Timing and pacing: display durations, response windows, timeouts, replay
  rules, and progress display. For replications, take values from the source
  study; otherwise document which values are defaults.
- Participant-visible feedback and reward: what participants learn about
  correctness, payoff, and progress, and how the final reward is explained.
- Completion states: success, rejection, consent rejection, timeout,
  technical failure, and participant abort behavior.

## Rigor scaling

The purpose recorded in PLAN.md sets the expected depth: a formal experiment
or replication specifies every stage and parameter; a pilot or demo may leave
low-stakes fields at documented defaults. Never scale down the design-decision
matrix itself.

## Self-check before requesting the gate review

- Every matrix decision appears in the key-decisions table with a choice and
  status.
- The journey has no unaccounted stages.
- The analysis plan is concrete enough to write the analysis scripts from.
- Replication deviations from the source study are listed as negotiation
  points, not buried in prose.
