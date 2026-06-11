---
name: psynet-synchronous-experiments
description: Design and implement PsyNet synchronous experiments using cohort, grouping, barrier, waiting-room, and recruiter coordination patterns without assuming websocket interaction.
authors: [pmcharrison]
---

# Implement synchronous PsyNet experiments

Use this skill when a PsyNet experiment needs participants to be present,
grouped, sequenced, or released together, but does not necessarily need
continuous websocket interaction inside a trial.

If participants exchange live actions or messages within a trial, also read
`psynet-realtime-synchronous-experiments/SKILL.md`.

## Required reads

- Read `psynet-experiment-implementation/SKILL.md` for the general PsyNet
  implementation workflow and validation expectations.
- Read `references/source-notes.md` for the source map, platform notes, and
  practical caveats behind this skill.
- Inspect current PsyNet docs and demos before coding:
  `~/PsyNet/docs/tutorials/synchronization.rst`,
  `~/PsyNet/docs/api/sync.rst`,
  `~/PsyNet/demos/experiments/simple_sync_group/`,
  `~/PsyNet/demos/experiments/create_rate_sync/`,
  `~/PsyNet/demos/experiments/rock_paper_scissors/`,
  `~/PsyNet/demos/experiments/sync_quorum/`, and
  `~/PsyNet/demos/experiments/gibbs_within_sync/`.

## Choose the synchronization model

1. Classify the design before coding:
   - cohort/quorum: participants must enter a phase together;
   - grouped trials: group members should receive the same node or trial order;
   - phase barriers: participants work independently, then wait for partners;
   - delayed/session launch: recruitment or access opens at a specific time;
   - live interaction: use the realtime websocket skill as well.
2. Prefer PsyNet server-side grouping and barriers over browser-side polling or
   custom JavaScript for shared state.
3. Decide what happens to late arrivals, no-shows, dropouts, and overflow
   participants before implementing the happy path.
4. Size the study in whole groups. Align `target_n_participants`,
   `initial_recruitment_size`, platform slots, and any over-recruitment buffer.
5. Make waiting fair: explain the expected wait, cap waits with
   `max_wait_time`, and provide filler tasks or a paid exit when waits can be
   long.

## PsyNet implementation hints

- Use `SimpleGrouper(group_type=..., initial_group_size=...)` to create cohorts
  and `GroupBarrier(id_=..., group_type=...)` to release group members together.
- Use `GroupBarrier(on_release=...)` for atomic shared updates such as role
  assignment, scoring, aggregation, or recording round outcomes.
- Sort `sync_group.participants` by participant ID before deterministic role
  assignment; PsyNet does not guarantee the stored order.
- Use `sync_group_type` on trial makers when all group members should follow the
  leader's node allocation and trial sequence.
- Put additional `GroupBarrier`s inside `Trial.show_trial` for phase boundaries
  such as submit, rate, reveal, score, or bonus computation.
- Read partner state through `participant.sync_group.participants`,
  participant vars, trial vars, node vars, or `on_release` outputs. Do not let
  the browser decide shared experiment state.
- Use `GroupCloser(group_type=...)` before regrouping participants with the same
  `group_type`.
- Use `join_existing_groups=True` only with a task-specific `join_criterion`
  that rejects stale, completed, or unsuitable groups.
- For lobbies/quorums, combine `SimpleGrouper(..., waiting_logic=...)` with
  filler work via `trial_maker.custom(...)`, as in `sync_quorum`.
- For chain or Gibbs designs, distinguish true co-presence from async
  across-participant chains. Use `wait_for_networks=True` when participants may
  otherwise exit while async network growth is still pending.
- Use `ChatRoom(room_id=f"group_{participant.sync_group.id}")` only for
  participant communication; keep phase advancement and scoring in barriers.
- For synchronous chain or rolling-inventory designs, make node readiness depend
  on the active group size, not only a fixed `trials_per_node`, so a generation
  does not spawn before all current group members have submitted.
- Keep rolling shared state analyzable in node definitions or trial answers:
  condition, generation, parent/original network IDs, visible option IDs,
  ancestry/children, proposal counts, and selection/adoption records.
- For timed phases, prefer participant-facing wait pages that show which
  anonymous group members are done or pending. This reduces confusion and makes
  stalled-partner behavior easier to debug.

## Recruitment and platform design

- Treat Prolific, Connect, MTurk, Cint, or Lucid as recruitment layers. PsyNet
  should still own the lobby, grouping, timeout, overflow, and completion logic.
- Prefer Prolific or CloudResearch Connect for small scheduled cohorts because
  they support participant IDs, targeted recontact, messages, quotas, and manual
  review workflows.
- Put session time, time zone, expected waiting window, device/audio
  requirements, no-show policy, and partial-payment policy in the study
  description and participant instructions.
- Store platform IDs with PsyNet participant and group metadata so no-shows,
  partial completions, bonuses, and follow-up waves can be audited.
- For Prolific, plan around no built-in appointment scheduling for focus groups:
  use participant groups, allowlists, messages, waves, and manual/bonus payment
  review when participants spend time but cannot be grouped.
- For Connect, record Connect IDs, use included participants/groups for waves,
  and use completion or partial-complete redirects that match the PsyNet exit
  path.
- Use MTurk only when the researcher accepts custom operational work for timing,
  qualifications, reminders, and partial compensation.
- Avoid Cint/Lucid for tightly synchronized small groups unless the study has
  panel/API support and explicit redirect/status accounting.

## Validation

- Run `psynet test local` with at least as many bots as the group size, plus
  extra bots for late-arrival or top-up paths.
- Use serial bot tests with `advance_past_wait_pages(bots)` for deterministic
  barrier progression; use concurrent bot runs when arrival races matter.
- Assert group formation, active group size, role assignment, shared node/trial
  IDs, barrier IDs, `on_release` side effects, and failed/overflow exits.
- Test dropout and top-up behavior, not only a complete group that finishes.
- For one-human manual sync testing, a development-only route or scheduled task
  may launch companion bots to fill the group. Disable or guard this path before
  real deployment.
- For participant-facing waiting rooms or multi-browser behavior, collect
  separate browser-context evidence. Use `record-participant-video/SKILL.md` for
  challenge evidence or participant-flow recordings.
- Inspect exported data to confirm group IDs, platform IDs, roles, phase
  timestamps, responses, failures, and partial-completion reasons are analyzable.

## Common failures

- Do not call a websocket/chatroom experiment "synchronized" unless barriers or
  another server-side mechanism actually coordinate phase advancement.
- Do not reuse an active `group_type` without `GroupCloser`.
- Do not leave default wait limits in place for real recruitment sessions
  without checking whether they are humane and scientifically appropriate.
- Do not assume top-ups are safe; define exactly which groups may accept late
  participants.
- Do not set recruitment targets that leave stranded participants unable to form
  a full group.
- Do not auto-reject participants who waited or were stranded by no-shows; plan
  a platform-compliant return, partial payment, or manual review path.
