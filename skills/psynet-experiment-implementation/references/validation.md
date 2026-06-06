# Validation

Choose validation that matches the risk of the implementation.

For a small experiment, useful checks include:

```bash
python experiment.py
psynet test local
```

For interactive flow checks:

```bash
psynet debug local
```

Then open the generated ad page URL and progress through the participant flow.

Record what you ran and what happened in the challenge attempt's `evidence/`
folder. If a command cannot run because system services are unavailable, record
that clearly rather than pretending validation passed.
