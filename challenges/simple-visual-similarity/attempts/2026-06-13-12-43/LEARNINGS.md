# Learnings

## Passing `bot_response=None` silently bypasses `get_bot_response` and `format_answer`

When subclassing an `OptionControl` (e.g. `KeyboardPushButtonControl`), passing
`bot_response=None` is treated as an explicit bot answer of `None` rather than
"unset". `Control.call__get_bot_response` only calls `get_bot_response` when
`_bot_response == NoArgumentProvided`, so `bot_response=None` made simulated bots
submit `answer=None` directly, bypassing the control's `format_answer` and storing
a non-dict trial answer. The fix was to omit `bot_response` entirely so
`get_bot_response` runs and routes the bot through `format_answer` (which computes
reaction time from the event log). Returning `BotResponse(raw_answer=..., metadata={"event_log": ...})`
without `answer` is the pattern that keeps the bot path identical to the browser path.

*Actions:*

- **PsyNet:** The `bot_response` parameter conflates "no bot response provided" with an explicit `None` answer, which is an easy footgun when a custom control needs its `get_bot_response`/`format_answer` to run. Consider documenting this in the `OptionControl`/`Control` docstrings or warning when `bot_response=None` is passed to a control that overrides `get_bot_response`. Confidence: high. Impact: medium. Status: completed. Notes: Implemented as PsyNet MR !1088 (https://gitlab.com/PsyNetDev/PsyNet/-/merge_requests/1088) — adds the warning in `Control.call__get_bot_response`, clarifies the `bot_response` docstring, and adds an isolated unit test; reviewer Peter Harrison. Open pending maintainer review/merge.

## Reaction time can be derived from the native event log without custom JS

A `GraphicPrompt` with `prevent_control_response=True` plus a stimulus frame with
`activate_control_response=True` fires `responseEnable` exactly at stimulus onset,
and `KeyboardPushButtonControl` logs `pushButtonClicked`. Computing
`localTime(pushButtonClicked) − localTime(responseEnable)` in `format_answer`
yields stimulus-onset-to-response reaction time with no bespoke timing JavaScript,
matching the psychophysics skill's guidance.

*Actions:*

- **PsyNetSkills:** The `psychophysics` skill recommends event-log reaction-time extraction but does not show a concrete recipe. Consider adding a short worked example (GraphicPrompt frame `activate_control_response` + `responseEnable`/`pushButtonClicked` event-log diff) to the psychophysics skill. Confidence: medium. Impact: medium. Status: completed. Notes: Added a "Reaction time from the native event log" worked example (wiring + `format_answer` recipe + simulation note) to `.cursor/skills/psychophysics/SKILL.md` on this attempt branch (PR #241).

## Notebook tooling (matplotlib/jupyter/nbconvert) is not in the PsyNet venv

The canonical analysis notebook needs `matplotlib`, `jupyter`, and `nbconvert`,
none of which ship with the PsyNet editable install. They had to be installed
manually (`uv pip install matplotlib jupyter nbconvert nbformat ipykernel`) before
the analysis notebook could be executed. This is generally needed for any
experiment-implementation attempt that produces a canonical analysis notebook.

*Actions:*

- **PsyNetSkills:** Consider adding the analysis-notebook tooling to the cloud-agent environment setup (or documenting the install command in the experiment-implementation evidence reference) so attempts do not each rediscover the missing dependencies. Confidence: high. Impact: medium. Status: completed. Notes: Documented the install command (`uv pip install matplotlib jupyter nbconvert nbformat ipykernel`) and headless-execute step in `psynet-experiment-implementation/SKILL.md` and `attempt-challenge/references/experiment-evidence.md` (PR #241). The persistent fix — baking the tooling into the cloud-agent environment — still needs an env-setup agent run from Cursor web.

## Dashboard truncates text files >100KB, breaking notebook `transform.Unmarshal`

The dashboard export (`psynetsk_tools/dashboard.py`, `max_bytes = 100_000`)
truncates the inline `content` of any text file, including `.ipynb`. The
`challenges/attempt.html` template then calls `transform.Unmarshal` on the
notebook content unconditionally, so a truncated (and therefore invalid-JSON)
`analysis.ipynb` crashes the Hugo build with
`unmarshal failed: invalid character '\n' in string literal`. An executed
analysis notebook with embedded plot PNGs easily exceeds 100KB. The workaround
here was to lower the figure DPI so the notebook stays under ~100KB; without that
the dashboard PR preview build fails.

*Actions:*

- **PsyNetSkills:** Make `challenges/attempt.html` resilient to truncated/unparseable notebook content — guard the `transform.Unmarshal` (e.g. only unmarshal when the file is not `truncated`, or wrap in a way that degrades to a download link) so a large analysis notebook cannot break the whole dashboard build. Confidence: high. Impact: high. Status: considering.
- **PsyNetSkills:** Document the ~100KB inline limit in the experiment-evidence reference and advise keeping `analysis.ipynb` small (low-DPI inline figures, or link out large figures), so attempts do not unknowingly produce a notebook that breaks the preview build. Confidence: high. Impact: medium. Status: completed. Notes: Documented the ~100KB inline-truncation limit, its consequence (truncated notebook = invalid JSON = broken attempt-page render / preview build), and both mitigations (low-DPI inline figures or link out large figures) in `attempt-challenge/references/experiment-evidence.md` (PR #241).

## Playwright needs its bundled ffmpeg for video recording

`@playwright/test` records video via a separate ffmpeg binary that is not the
system `ffmpeg`; the first recorded run failed with "Video rendering requires
ffmpeg binary" until `npx playwright install ffmpeg` was run. Worth pre-installing
for participant-flow video evidence.

*Actions:*

- **PsyNetSkills:** Consider noting `npx playwright install ffmpeg` in the `record-participant-video` skill for the JavaScript Playwright path, since system ffmpeg alone is insufficient for Playwright's built-in video recording. Confidence: high. Impact: low. Status: considering.
