# Learnings

## PsyNet local launch requires `source_code.zip` ignore coverage

`psynet test local` generated `source_code.zip` during launch checks and stopped
until that file was listed in the experiment `.gitignore`.

*Actions:*
- **PsyNetSkills:** Update the attempt challenge guidance to mention
  `source_code.zip` alongside the standard experiment support files when
  creating PsyNet challenge attempts. Confidence: high. Status: considering.

## Export outside the experiment directory can hit local permissions

`psynet export local --legacy --path ../../evidence/...` produced database export
output but failed when creating parent directories outside the experiment folder.
Exporting into an in-experiment path and then packaging the CSVs into
`evidence/data.zip` worked.

*Actions:*
- **PsyNetSkills:** Add a note to experiment evidence guidance recommending an
  in-experiment export path followed by copying or zipping evidence into the
  attempt folder. Confidence: medium. Status: considering.

## Review condition summaries before treating evidence as final

The first analysis summary showed that the main block only contained
happy-coded targets. Reviewing the summary table before finalizing evidence made
the condition imbalance visible and led to a balanced manifest across happy and
angry targets.

*Actions:*
- **PsyNetSkills:** Encourage challenge attempts to inspect analysis summaries
  for condition coverage, not only whether scripts run successfully. Confidence:
  high. Status: considering.
