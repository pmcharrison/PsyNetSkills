# Validation

Choose validation that matches the risk of the implementation.

For a small experiment, useful checks include:

```bash
python experiment.py
psynet test local
```

For challenge attempts and other work that needs performance evidence, run a
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
If the experiment customizes `run_bot`, preserve `bot=None` support and delegate
to `super().run_bot(...)` for framework-created bots; `psynet performance-test`
calls `exp.run_bot(time_factor=...)` without passing a bot object.

For interactive flow checks:

```bash
psynet debug local
```

Then capture the generated ad page URL and use Playwright to progress through
the participant flow when feasible. Browser control is useful for quick
exploration, but Playwright should drive repeatable screenshots, assertions, and
participant recordings.
For grouped experiments, set explicit `max_wait_time` values on groupers and
barriers before recording participant flows; browser windows and headed
automation often enter sequentially, and default waits can be too short for
reliable evidence collection.

Record what you ran and what happened in the challenge attempt's `evidence/`
folder. If a command cannot run because system services are unavailable, record
that clearly rather than pretending validation passed.
