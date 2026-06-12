# Science section checklist (agent-facing)

Work through this checklist while drafting the Science section of PLAN.md. It
is a coverage rubric for you, the agent: write the section itself as readable
academic prose and do not copy these labels into PLAN.md.

## Coverage

Must be covered (raise with the user if underspecified; these are high-stakes
for scientific validity):

- **Research question**: the primary question in 1-2 precise sentences.
- **Scientific construct**: the psychological, behavioral, cultural,
  perceptual, social, or interaction process being measured.
- **Hypotheses or expected patterns**: directional predictions, exploratory
  goals, or a statement that the study is a technical demonstration. Do not
  assert that an effect exists or pre-judge results.
- **Question archetype**: name the family the question belongs to —
  threshold/psychophysics, judgment/rating, transmission/serial reproduction,
  representation recovery (e.g. GSP, MCMCP), generate-and-evaluate,
  interaction/game. The archetype drives paradigm candidates in the Method
  stage.
- **Conditions and independent variables**: condition names, manipulation
  levels, and whether labels are visible to participants or internal only.
- **Dependent variables**: response values, reaction times, recordings,
  interaction logs, choices, ratings, free text, or derived scores.
- **Stimulus domain**: what stimuli are, where they come from, how many are
  used, and why this set is sufficient for the current study stage.
- **Participant population**: intended population, inclusion/exclusion
  criteria, platform, and whether bots or simulations are only for local
  validation.
- **Interpretation boundary**: which claims are valid from local bots,
  simulations, pilots, or production participants, and which are not.
- **Canonical reference**: for replications/adaptations, the source study
  (see `literature-grounding.md`); otherwise an explicit statement that no
  canonical reference exists.

Cover when relevant to the paradigm:

- Adaptive or sequential logic: how later stimuli depend on earlier responses,
  stopping rules, and what counts as valid adaptation.
- Social or group dynamics: group size, matching logic, roles, information
  sharing, payoff coupling, and dropout assumptions.
- AI or hybrid participants: model role, prompt parity with human
  instructions, and whether AI data is analyzed separately.
- Ethical or domain constraints: sensitive stimuli, deception, consent
  language, debriefing, data minimization, and external approvals.

## Candidate framings (new science questions)

For a new science question, derive 2-3 distinct framings before drafting.
Vary the archetype where defensible (e.g. "A: one-shot judgment study; B:
serial-reproduction chain recovering the prior") and state for each: what it
measures, what it can claim, and its cost/complexity. Present them with a
recommendation and let the user pick or merge. Never silently lock a framing.

## Clarification prompts

Useful questions when the idea is underspecified:

- Which scientific result would make the study successful?
- Which simplifications are acceptable at this stage?
- What should reviewers avoid over-interpreting?
- What data field would be most damaging to omit?

## Self-check before requesting the gate review

- Every must-cover item above is addressed in prose or explicitly out of
  scope with a reason.
- The *In brief* paragraph is present and understandable without PsyNet or
  domain jargon.
- The key-decisions table matches the prose.
- All decisions taken without the user are in the decision log, marked
  overridable.
