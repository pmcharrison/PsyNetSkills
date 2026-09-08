# Learnings

## Plan review gate is explicit for experiment attempts

The experiment implementation workflow requires `PLAN.md` and a human approval pause before writing challenge code, so this attempt intentionally stops with metadata and planning artifacts only.

*Actions:*
- **PsyNetSkills:** Make sure experiment-implementation attempt dashboards distinguish plan-review pauses from incomplete failed attempts when `agent.json` has `ended_at: null`. Confidence: medium. Impact: low. Status: considering.

## Playwright dependencies should not be committed

Installing `@playwright/test` inside an attempt directory created a local `node_modules/` tree that was accidentally staged before being removed in a follow-up commit.

*Actions:*
- **PsyNetSkills:** Add `node_modules/`, `playwright-report/`, and `test-results/` to the attempt-template ignore guidance or challenge evidence instructions for Playwright-based participant evidence. Confidence: high. Impact: medium. Status: considering.

## Verify PsyNet remains editable after dependency work

The local PsyNet venv initially imported PsyNet from site-packages after dependency installation, so the editable install had to be restored with `uv pip install -e '.[dev,slack]'`.

*Actions:*
- **PsyNetSkills:** Add a post-dependency-install check to experiment attempt workflows: `python -c "import psynet; print(psynet.__file__)"` must resolve under `~/PsyNet/psynet/` before running PsyNet evidence commands. Confidence: high. Impact: medium. Status: considering.
