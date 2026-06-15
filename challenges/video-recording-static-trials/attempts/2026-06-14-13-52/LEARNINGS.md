# Learnings

## Keep interaction IDs selector-safe

Radio option values used directly as HTML IDs should avoid spaces and punctuation.
Using stable keys (`not_at_all`, `a_little`, `very_much`) prevented fragile
selector behavior in Playwright evidence scripts while preserving participant
labels separately.

*Actions:*
- **PsyNetSkills:** Add a short note to experiment-implementation guidance recommending selector-safe control values when IDs are reused in automation scripts. Confidence: high. Impact: medium. Status: considering.

## Avoid test/debug port collisions during mixed evidence + automated testing

Running `psynet debug local` in parallel with `psynet test local` caused launch
failures on port `5000` (`Address already in use`). Explicitly stopping the debug
session before rerunning tests resolved the issue.

*Actions:*
- **PsyNetSkills:** Add a checklist line in evidence workflows to stop active debug servers before running automated PsyNet test commands. Confidence: high. Impact: medium. Status: considering.

## Reduce post-delivery local patch churn

When an attempt is "almost done" but still needs multiple local fixes by a human,
the final handoff gate is too weak. A dedicated pre-handoff reproducibility pass
should confirm that the submitted branch is the same branch that actually passes
all required checks end-to-end.

*Actions:*
- **PsyNetSkills:** Add a mandatory pre-handoff command bundle that must be re-run on the final committed branch (`psynet test local`, required challenge checks, and `uv run psynetsk-validate`) immediately before handoff, and block handoff if any command fails. Confidence: high. Impact: high. Status: considering.
