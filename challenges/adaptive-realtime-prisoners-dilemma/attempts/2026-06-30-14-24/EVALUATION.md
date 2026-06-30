---
score:
---

# Evaluation

## Summary

Summarize the human evaluator's overall judgment.

## Strengths

-

## Weaknesses

-

## Criteria

If `CRITERIA.md` is present, ask the evaluator about each criterion and record
the result here.

- [ ]

## Notes

- Score and feedback should come from a human evaluator, captured
  conversationally when working with Cursor Cloud Agents.
- Evidence blockers from implementation:
  - `dallinger constraints generate` and `uv pip install scipy` were blocked by
    repeated PyPI connection resets in the Cursor Cloud VM.
  - `psynet debug local` could not launch for browser recording because debug
    prechecks require SciPy to be installed from `requirements.txt`.
  - `psynet performance-test local ...` failed to spawn before producing JSON
    output, so performance evidence is limited to the passing local bot test.
