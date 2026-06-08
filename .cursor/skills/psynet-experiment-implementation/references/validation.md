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
  --time-factor 0 \
  --json-output ../../evidence/performance.json
```

Adjust the JSON output path to match the attempt or project layout.

For interactive flow checks:

```bash
psynet debug local
```

Then open the generated ad page URL and progress through the participant flow.

Record what you ran and what happened in the challenge attempt's `evidence/`
folder. If a command cannot run because system services are unavailable, record
that clearly rather than pretending validation passed.
