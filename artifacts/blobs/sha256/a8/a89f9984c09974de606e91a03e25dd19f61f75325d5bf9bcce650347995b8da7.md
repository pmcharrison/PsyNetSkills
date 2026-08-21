# Export-before-teardown safety plan

This is a reviewed command plan only. Do not run export, destroy, teardown, or
AWS-affecting commands unless the deployment owner explicitly confirms the target
deployment and asks for execution.

## Global safety sequence

1. Confirm the experiment folder, app, server host, DNS host, and region against
   the live deployment owner's notes.
2. Verify an export exists in a durable experiment-owned `exports/` directory, or
   run the export command first.
3. Inspect the exported folder for the expected core files before running any
   destructive command.
4. Destroy the PsyNet app only after export verification passes.
5. Tear down the EC2 server only after app destruction is complete.
6. Run the regional EC2 verification command and save its output.

## Deployment: `ww-global-rhythm-val`

- Classification: `ready for teardown`
- Experiment folder: `/experiments/global-rhythm-validation`
- App name: `ww-global-rhythm-val`
- Server name: `ww-global-rhythm-val`
- Server host: `ww-global-rhythm-val.cap-experiments.com`
- DNS host: `ww-global-rhythm-val.cap-experiments.com`
- Region: `us-east-2`
- Current known status: export appears present; final teardown verification is
  not recorded.
- Expected export path: `/experiments/global-rhythm-validation/exports/ww-global-rhythm-val-2026-06-07`
- Evidence that export already exists: inventory reports `Participant.csv`,
  `Response.csv`, `Trial.csv`, and `source_code.zip` in the expected export
  folder.
- Blockers or uncertainties requiring human confirmation: confirm that the
  reported export folder is complete and copied to any required long-term
  storage before destructive commands run.

### Export verification gate

Run these non-destructive checks first:

```bash
cd /experiments/global-rhythm-validation
test -d /experiments/global-rhythm-validation/exports/ww-global-rhythm-val-2026-06-07
test -f /experiments/global-rhythm-validation/exports/ww-global-rhythm-val-2026-06-07/Participant.csv
test -f /experiments/global-rhythm-validation/exports/ww-global-rhythm-val-2026-06-07/Response.csv
test -f /experiments/global-rhythm-validation/exports/ww-global-rhythm-val-2026-06-07/Trial.csv
test -f /experiments/global-rhythm-validation/exports/ww-global-rhythm-val-2026-06-07/source_code.zip
```

If any check fails, export before teardown:

```bash
cd /experiments/global-rhythm-validation
psynet export ssh \
  --app ww-global-rhythm-val \
  --server ww-global-rhythm-val.cap-experiments.com \
  --path /experiments/global-rhythm-validation/exports
```

### Destructive commands (do not run until gate passes)

Destroy app command:

```bash
cd /experiments/global-rhythm-validation
psynet destroy ssh \
  --app ww-global-rhythm-val \
  --server ww-global-rhythm-val.cap-experiments.com
```

EC2 teardown command:

```bash
dallinger ec2 teardown \
  --name ww-global-rhythm-val \
  --region us-east-2 \
  --dns-host ww-global-rhythm-val.cap-experiments.com
```

Final verification command:

```bash
dallinger ec2 list instances --all --region us-east-2 | rg 'ww-global-rhythm-val|Name|Instance'
```

## Deployment: `ww-bach-tapping-pilot`

- Classification: `export first`
- Experiment folder: `/experiments/bach-tapping-pilot`
- App name: `ww-bach-tapping-pilot`
- Server name: `ww-bach-tapping-pilot`
- Server host: `ww-bach-tapping-pilot.cap-experiments.com`
- DNS host: `ww-bach-tapping-pilot.cap-experiments.com`
- Region: `us-east-1`
- Current known status: participants were recruited yesterday; no export folder
  was found.
- Expected export path: `/experiments/bach-tapping-pilot/exports/<export-folder-created-by-psynet>`
- Evidence that export already exists: none in the inventory.
- Blockers or uncertainties requiring human confirmation: confirm recruitment is
  closed and no participant session is still active before exporting and
  destroying the app.

### Export verification gate

Run the export before any destructive command:

```bash
cd /experiments/bach-tapping-pilot
psynet export ssh \
  --app ww-bach-tapping-pilot \
  --server ww-bach-tapping-pilot.cap-experiments.com \
  --path /experiments/bach-tapping-pilot/exports
```

Then verify that a durable export folder was created:

```bash
cd /experiments/bach-tapping-pilot
ls -la /experiments/bach-tapping-pilot/exports
find /experiments/bach-tapping-pilot/exports -maxdepth 2 -type f \( -name 'Participant.csv' -o -name 'Response.csv' -o -name 'Trial.csv' -o -name 'source_code.zip' \)
```

### Destructive commands (do not run until gate passes)

Destroy app command:

```bash
cd /experiments/bach-tapping-pilot
psynet destroy ssh \
  --app ww-bach-tapping-pilot \
  --server ww-bach-tapping-pilot.cap-experiments.com
```

EC2 teardown command:

```bash
dallinger ec2 teardown \
  --name ww-bach-tapping-pilot \
  --region us-east-1 \
  --dns-host ww-bach-tapping-pilot.cap-experiments.com
```

Final verification command:

```bash
dallinger ec2 list instances --all --region us-east-1 | rg 'ww-bach-tapping-pilot|Name|Instance'
```

## Deployment: `ww-old-listening-test`

- Classification: `needs human confirmation`
- Experiment folder: unknown
- App name: `ww-old-listening-test`
- Server name: `ww-old-listening-test`
- Server host: `ww-old-listening-test.cap-experiments.com`
- DNS host: unknown
- Region: unknown
- Current known status: inventory reports only a temporary export path,
  `/tmp/relative-export`; this is not sufficient evidence for teardown.
- Expected export path: blocked until a durable experiment folder is confirmed;
  use `<confirmed-experiment-folder>/exports/<export-folder-created-by-psynet>`.
- Evidence that export already exists: none usable. `/tmp/relative-export` may
  be relative, temporary, or from the wrong host.
- Blockers or uncertainties requiring human confirmation: confirm experiment
  folder, DNS host, region, server ownership, and a durable export destination.

### Export verification gate

Do not export, destroy, or tear down until the missing metadata is confirmed.
After confirmation, use this template and replace every placeholder:

```bash
cd <confirmed-experiment-folder>
psynet export ssh \
  --app ww-old-listening-test \
  --server <confirmed-dns-host> \
  --path <confirmed-experiment-folder>/exports
```

Then verify a durable export:

```bash
test -d <confirmed-experiment-folder>/exports/<confirmed-export-folder>
find <confirmed-experiment-folder>/exports/<confirmed-export-folder> -maxdepth 1 -type f
```

### Destructive commands (do not run until gate passes)

Destroy app command:

```bash
BLOCKED: psynet destroy ssh --app ww-old-listening-test --server <confirmed-dns-host>
```

EC2 teardown command:

```bash
BLOCKED: dallinger ec2 teardown --name ww-old-listening-test --region <confirmed-region> --dns-host <confirmed-dns-host>
```

Final verification command:

```bash
BLOCKED: dallinger ec2 list instances --all --region <confirmed-region> | rg 'ww-old-listening-test|Name|Instance'
```

## Regional EC2 verification commands

Run these after app destruction and EC2 teardown, grouped by region:

### `us-east-1`

```bash
dallinger ec2 list instances --all --region us-east-1 | rg 'ww-bach-tapping-pilot|Name|Instance'
```

### `us-east-2`

```bash
dallinger ec2 list instances --all --region us-east-2 | rg 'ww-global-rhythm-val|Name|Instance'
```

### Unknown region

`ww-old-listening-test` has no safe regional EC2 verification command until the
region is confirmed by a human.

