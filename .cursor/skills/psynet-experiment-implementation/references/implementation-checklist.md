# Implementation section checklist (agent-facing)

Work through this checklist while drafting the Implementation section of
PLAN.md. This section identifies the technical choices that need human review
before coding; it is not a line-by-line coding recipe. Do not write experiment
code during planning.

## Coverage

- **PsyNet version and base demo**: target PsyNet checkout and the closest
  demo path (see `experiment-patterns.md`); what must remain unchanged from
  the base paradigm.
- **Experiment architecture**: page-only, static trials, chain/network,
  adaptive, synchronous multi-participant, AI/hybrid, or a combination. This
  must match the Method section's key decisions.
- **Core PsyNet mapping**: intended use of timeline pages, trial classes,
  nodes, trial makers, modules, groupers, assets, recruiters, and controls.
- **Configuration strategy**: which parameters live in `config.txt`, class
  variables, manifests, environment variables, or testing fixtures.
- **Stimulus and asset pipeline**: manifest format, asset generation or
  download, licensing and source metadata, reproducibility, and replacement
  of demo assets.
- **Data schema**: fields saved per participant, trial, node, group,
  recording, and AI call; include field names when possible. Check that every
  dependent variable in the Science section has a concrete field.
- **Bot and simulation path**: bot responses, deterministic vs. stochastic
  simulation, and parity between bot and browser submissions.
- **Testing and evidence plan**: expected `psynet test local` behavior, custom
  assertions, participant video path, performance checks, export checks, and
  analysis script checks (see `validation.md`). Experiments in this workflow
  run, test, and record evidence locally; do not plan a real deployment, and
  use only local ephemeral PsyNet/Dallinger defaults for credentials.

Cover when relevant:

- Custom frontend justification: why built-in PsyNet pages, controls,
  graphics, events, or modules are insufficient. Prefer native PsyNet
  mechanisms; bespoke JavaScript is a last resort.
- External API integration: mock-first behavior, timeout/retry/failure
  handling, prompt and version logging, secret handling.
- Performance envelope: expected concurrency, duration, load-test bot count.
- Translation/localization: use `prepare-for-translation` for multilingual or
  cross-cultural experiments.

## Escalation rule

If the gap between the planned design and what PsyNet can natively express is
large (custom frontend, specialised hardware, a large stimulus corpus needing
prior preparation, or complex external integrations), stop and consult the
user before approving this section: suggest compiling the experimental
materials as a separate preparatory project first.

## Self-check before requesting the gate review

- The architecture is consistent with every Method key decision.
- Each dependent variable maps to a saved field.
- The testing and evidence plan names the commands and artifacts that will
  prove the experiment works locally.
- No experiment code has been written yet.
