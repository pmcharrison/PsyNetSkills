---
name: review-skill-candidates
description: Review unreviewed skill candidates, check overlap, approve or reject them, and route approved work through existing skill-creation procedures. Use when triaging mined skill candidates from attempts or learning actions.
---

# Review skill candidates

Review, triage, approve, reject, or implement unreviewed skill candidates produced
by `mine-skill-candidates`, or list unreviewed draft skills.

## Goal

Turn unreviewed candidates into clear decisions. A review may approve a new
skill, recommend an extension to an existing skill, defer for more evidence,
reject the candidate, or implement an approved change through `create-skill`.

## Required reads

- Read `skill-candidates.yaml` when it exists.
- Read the candidate's cited action IDs, `LEARNINGS.md`, `EVALUATION.md`, or
  dashboard source paths only as needed to verify the rationale.
- Read `skill-overlap-review/SKILL.md` before deciding disposition.
- Read `~/PsyNet/.cursor/skills/create-skill/SKILL.md` and the workshop
  `create-skill` addendum before implementing any approved skill change.

## Workflow

1. Collect review targets from `skill-candidates.yaml` (`status: unreviewed`).
2. Present a concise review queue grouped by urgency and proposed disposition.
3. Skip or batch low-value items before deep review:
   - mark `triage: small_edit` items as `rejected`, `deferred`, or route them to
     a one-sentence owner-skill edit when the fix is obvious;
   - only promote small edits when multiple sources reveal the same recurring
     workflow gap;
   - leave `trace_status: sorted` once the information has been considered.
4. For each candidate under review, verify:
   - evidence sources exist and support the claimed problem or pattern;
   - the candidate is general enough to recur;
   - the trigger is clear;
   - the proposed procedure would change future agent behavior;
   - the expected benefit justifies another skill or skill edit.
5. Run `skill-overlap-review/SKILL.md` and record the overlap disposition:
   - `replacement`: reject the candidate or point to the existing skill;
   - `extension`: approve an update to the owner skill;
   - `pointer`: approve only if the candidate has distinct ownership;
   - `combination`: approve a choreography skill that points to owner skills;
   - `new`: approve a new skill only if the necessity filter passes.
6. Update the candidate status:
   - `approved` when the reviewer wants the change but not immediate editing;
   - `implemented` after the corresponding skill change is committed;
   - `rejected` when it is too narrow, duplicative, or unsupported;
   - `deferred` when more evidence is needed.
7. Update trace fields:
   - add reviewed action IDs, attempt paths, `LEARNINGS.md`, and
     `EVALUATION.md` paths to `source_ids` or `traced_sources`;
   - set `trace_status: sorted` when the source has been handled;
   - keep review status separate from functional skill execution.
8. If implementing, invoke `create-skill/SKILL.md`. Do not bypass author
   identification, overlap reporting, or validation.

## Review output

For each reviewed item, record:

- decision and status;
- triage and trace status;
- overlap disposition;
- evidence checked;
- files changed, if any;
- follow-up owner or next action.

## Rules

- Less is better than more. Reject weak candidates even if they sound useful.
- Do not turn isolated challenge feedback into a general skill.
- Do not copy hidden criteria, private attempt material, secrets, or participant
  data into skills or candidate summaries.
- Do not implement multiple unrelated approved candidates in one commit unless
  the user explicitly asks for a batch.
- Keep review metadata separate from functional skill instructions.

## Validation

After changing candidates or skills, run:

`uv run psynetsk-validate`
