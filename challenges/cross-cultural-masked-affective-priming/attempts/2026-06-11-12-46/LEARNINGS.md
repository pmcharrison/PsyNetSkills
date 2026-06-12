# Learnings

## PsyNet local launch requires `source_code.zip` ignore coverage

`psynet test local` generated `source_code.zip` during launch checks and stopped
until that file was listed in the experiment `.gitignore`.

*Actions:*
- **PsyNetSkills:** Update the attempt challenge guidance to mention
  `source_code.zip` alongside the standard experiment support files when
  creating PsyNet challenge attempts. Confidence: high. Impact: low. Status: considering.
## Export outside the experiment directory can hit local permissions

`psynet export local --legacy --path ../../evidence/...` produced database export
output but failed when creating parent directories outside the experiment folder.
Exporting into an in-experiment path and then packaging the CSVs into
`evidence/data.zip` worked.

*Actions:*
- **PsyNetSkills:** Add a note to experiment evidence guidance recommending an
  in-experiment export path followed by copying or zipping evidence into the
  attempt folder. Confidence: medium. Impact: low. Status: considering.
## Review condition summaries before treating evidence as final

The first analysis summary showed that the main block only contained
happy-coded targets. Reviewing the summary table before finalizing evidence made
the condition imbalance visible and led to a balanced manifest across happy and
angry targets.

*Actions:*
- **PsyNetSkills:** Encourage challenge attempts to inspect analysis summaries
  for condition coverage, not only whether scripts run successfully. Confidence:
  high. Impact: high. Status: considering.
## Cross-cultural experiments should trigger translation readiness during implementation

The experiment was described as cross-cultural, but participant-facing strings
were not marked for translation during the first implementation pass. The
existing `prepare-for-translation` skill owned the detailed workflow, but the
attempt and implementation skills did not make that trigger hard to miss.

*Actions:*
- **PsyNetSkills:** Added pointer rules to `attempt-challenge` and
  `psynet-experiment-implementation` so cross-cultural, cross-national,
  multilingual, and international experiments invoke translation readiness while
  the experiment is being implemented, before final evidence collection.
  Confidence: high. Impact: high. Status: completed.
