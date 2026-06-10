# Learnings

## Prefer minimal participant walkthroughs for long rating studies

A long recording added little value for this challenge because the participant flow is highly repetitive once the first rating trial is visible and working.

*Actions:*
- **PsyNetSkills:** Update the attempt or recording guidance to explicitly allow short representative participant recordings for long repetitive rating experiments, while relying on automated validation for completeness. Confidence: high. Status: considering.

## Local export and dashboard monitor friction in debug mode

The experiment itself ran locally, but `psynet export local` depended on dashboard configuration that was not available in this environment, and the dashboard monitor routes required authentication that was not documented in the challenge workflow.

*Actions:*
- **PsyNetSkills:** Add Cursor Cloud notes for collecting `monitor.html` and `data.zip` when dashboard auth is unavailable in local debug mode. Confidence: medium. Status: considering.

## Questionnaire reconstructions need a clearer paper trail

The evaluator wanted each implemented questionnaire to be backed by a downloaded source paper or instrument reference stored inside the attempt, so a reviewer can verify wording and scoring decisions without chasing external links.

*Actions:*
- **PsyNetSkills:** Update replication-oriented attempt guidance to require a local reference file for each reconstructed questionnaire or scoring instrument when licensing allows it, plus explicit cross-references in the methods note. Confidence: high. Status: considering.

## Escalate when stimulus fidelity is below the requested bar

The evaluator judged the additive-synthesis piano and strings timbres as too poor to count as adequate analogues of the original stimuli. When realistic sound fonts or sample libraries are unavailable, the attempt workflow should favor an explicit discussion with the user over quietly proceeding with obviously weak substitutes.

*Actions:*
- **PsyNetSkills:** Add a rule for experiment-replication attempts: if the requested stimulus fidelity depends on unavailable local assets, stop and discuss acceptable fallback options with the user before finalizing the implementation. Confidence: high. Status: considering.

## Prefer built-in simulation and richer analysis deliverables

The evaluator expected the attempt to lean on PsyNet's native simulation capabilities and to invest more in analysis outputs, including installed dependencies, figures, and ideally a notebook-style report.

*Actions:*
- **PsyNetSkills:** Clarify in experiment-replication guidance that custom simulation scripts should be a fallback, not the default, when PsyNet already provides a suitable simulation path. Confidence: medium. Status: considering.
- **PsyNetSkills:** Raise the default analysis bar for replication attempts to include dependency installation when needed, figure generation, and a notebook or notebook-like report when the challenge asks for close analytical replication. Confidence: high. Status: considering.
