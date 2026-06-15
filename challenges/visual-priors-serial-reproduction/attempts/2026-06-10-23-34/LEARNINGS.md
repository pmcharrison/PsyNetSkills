# Learnings

## Local export credential path

`psynet export local` with the default dashboard-download path still read
`dashboard_password` from local config even when `--username` and `--password`
were provided. The legacy local exporter avoided this for the challenge evidence
run.

*Actions:*
- **PsyNet:** Make `psynet export local --username/--password` feed the dashboard request, or document that those options do not apply before the config lookup. Confidence: medium. Impact: low. Status: considering.

## Use absolute evidence paths for PsyNet exports

The legacy exporter failed when given a relative path from the nested experiment
directory because a subprocess resolved it from a different working directory.
Using an absolute path under the attempt evidence directory made the export
repeatable.

*Actions:*
- **PsyNetSkills:** Recommend absolute paths for `psynet export local --path` in challenge evidence instructions. Confidence: high. Impact: low. Status: completed. Notes: Added absolute-path guidance to the experiment evidence checklist and validation reference.

## Avoid unrequested task elements

The evaluation noted that the fixation cross was not explicitly mentioned in the
challenge description. Future attempts should avoid adding procedure elements
unless they are specified by the instructions or clearly required by the
framework.

*Actions:*
- **PsyNetSkills:** Add attempt guidance reminding agents not to infer extra participant-facing task elements from generic experiment conventions. Confidence: high. Impact: medium. Status: completed. Notes: Added explicit psychophysics guidance not to add unrequested participant-facing task elements.

## Interpret schematic figure sizes cautiously

The evaluation noted that the dot appeared too large, likely because schematic
figures exaggerate small objects for visibility. Future visual experiment
implementations should distinguish schematic clarity from intended stimulus
scale.

*Actions:*
- **PsyNetSkills:** Add visual-experiment guidance to treat schematic element sizes as approximate unless the challenge text or source gives measurements. Confidence: high. Impact: medium. Status: completed. Notes: Added schematic-size guidance to the dedicated psychophysics skill.
