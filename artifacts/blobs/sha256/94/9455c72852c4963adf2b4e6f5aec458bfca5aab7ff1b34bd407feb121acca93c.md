# AutoCog-compatible human decision-making task

This directory contains a small generator and its generated PsyNet experiment.

Run from this directory:

```bash
python3 -m autocog_compatible_human_dm_task.generate_experiment \
  autocog_compatible_human_dm_task/example_config.py \
  generated_experiment
```

Then run PsyNet checks from `generated_experiment/`.
