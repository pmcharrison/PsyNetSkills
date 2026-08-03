# Validation

Use this reference before claiming a PsyNet experiment is functionally complete
or before collecting final challenge evidence. It owns final check commands,
evidence path conventions, and PsyNet-specific validation pitfalls. For
day-to-day backend or frontend testing strategy, use
`develop-experiment-back-end/SKILL.md` and
`develop-experiment-front-end/SKILL.md`.

## Functional checks

Run functional checks from the experiment directory:

```bash
python experiment.py
psynet test local
```

## Performance evidence

For challenge attempts and other work that needs performance evidence, run this
sustained load test after functional checks pass. Do not rely on experiment
defaults such as `test_n_bots = 1`. Prefer `--audit` so results land in the
audit packet immediately:

```bash
# From experiment root (./audit/) or challenge attempt root
psynet performance-test local \
  --n-bots 40 \
  --duration-minutes 5 \
  --time-factor 1.0 \
  --audit

# From code/<slug>/ in a challenge attempt (packet is ../..)
psynet performance-test local \
  --n-bots 40 \
  --duration-minutes 5 \
  --time-factor 1.0 \
  --audit ../..
```

That writes `<AUDIT_ROOT>/artifacts/performance.json`. Use `--json-output` only
for a custom non-audit path. Prefer an absolute `--audit` path when PsyNet may
run from a temporary deployment directory.
If the experiment customizes `run_bot`, preserve `bot=None` support and delegate
to `super().run_bot(...)` for framework-created bots; `psynet performance-test`
calls `exp.run_bot(time_factor=...)` without passing a bot object.

Short smoke runs are fine while iterating or infrastructure-testing; write them
with `--audit` when you want the JSON in the packet. Prefer a sustained run
when claiming production-like performance evidence. Skip an expensive re-run
when a suitable `artifacts/performance.json` already exists for the current
implementation.

## Interactive evidence

```bash
psynet debug local
```

Capture the generated ad page URL. Browser control is acceptable for quick
exploration, but repeatable screenshots, assertions, and participant recordings
should be Playwright-driven. For challenge evidence or canonical participant
recordings, follow `record-participant-video/SKILL.md`.

For grouped experiments, set explicit `max_wait_time` values on groupers and
barriers before recording participant flows; browser windows and headed
automation often enter sequentially, and default waits can be too short for
reliable evidence collection.

## Evidence notes

For challenge attempts, the attempt root is the audit packet
(`docs/audit.md`): put review artifacts under `artifacts/`, analysis under
`analyses/`, and command logs under `logs/`. Keep `audit.json` in sync with
`psynet audit mark-present <artifact_id>` / blockers as files land (auto-detect
works from the attempt root).

Record what you ran and what happened in those directories. If a command cannot
run because system services are unavailable, record that clearly rather than
pretending validation passed.
