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
defaults such as `test_n_bots = 1`:

```bash
psynet performance-test local \
  --n-bots 40 \
  --duration-minutes 5 \
  --time-factor 1.0 \
  --json-output ../../evidence/performance.json
```

Adjust the JSON output path to match the attempt or project layout.
For export commands and commands that may spawn subprocesses, prefer an absolute
path under the attempt's `evidence/` directory; relative paths can resolve from a
temporary deployment directory rather than the experiment directory.
If the experiment customizes `run_bot`, preserve `bot=None` support and delegate
to `super().run_bot(...)` for framework-created bots; `psynet performance-test`
calls `exp.run_bot(time_factor=...)` without passing a bot object.

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

Record what you ran and what happened in the challenge attempt's `evidence/`
folder. If a command cannot run because system services are unavailable, record
that clearly rather than pretending validation passed.
