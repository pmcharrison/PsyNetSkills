# Experiment plan: <title>

- **Purpose:** <simple implementation / replication or adaptation / new
  science question> — <one line on what success means>.
- **Status:** <e.g. "Science approved, Method under review" — keep current;
  the full section status table lives in PLAN_DETAILS.md>.

<!--
This file is the human-readable plan rendered on the dashboard. Write it as
flowing prose a reviewer can absorb in one pass. Keep workflow scaffolding
(status table, key-decisions tables, decision log, exact technical
specification) in PLAN_DETAILS.md, which is the authoritative contract for
implementation. The two files must always agree; on conflict, fix it at
review. Scale length to the purpose: a simple demo needs a few paragraphs, a
formal experiment or replication proportionally more.
-->

## Science

<Plain-language prose: what the experiment is meant to learn and what it is
not allowed to claim. Background, research question, hypotheses, stimulus
domain, participant population, interpretation boundary. For replications,
state what was transcribed from the source study. If out of scope, one
sentence saying so and why.>

## Method

<Prose like a paper's Methods section: what participants experience from
arrival to completion, the design (conditions, within/between, assignment),
materials, timing and responses, quality controls, and the planned analysis.
Key structural choices — within vs. between, static vs. chain, synchronous
structure, AI involvement — should read naturally as part of the narrative.>

## Implementation

<Short prose or compact bullets: closest PsyNet demo, experiment
architecture, what is saved, and how the experiment is tested and recorded
locally. Keep exhaustive construct-level detail in PLAN_DETAILS.md.>

---

The full binding specification — section status, per-stage decision tables,
decision log, and the exact technical plan — is in `PLAN_DETAILS.md` next to
this file. Implementation must follow that file exactly. On the dashboard
attempt page, the detailed plan is rendered as a collapsed section at the end
of the page, reachable from the link below this plan.
