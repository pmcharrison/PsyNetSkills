# Learnings

## Plan gate for experiment attempts

Experiment implementation challenges require a committed `PLAN.md` and human review before coding, even when the user asks the agent to retry an attempt.

*Actions:*

- **PsyNetSkills:** Consider adding a short `/attempt-challenge` response template for experiment implementation retries that explains the plan-review pause and the expected next user action. Confidence: medium. Impact: low. Status: considering.

## Unique session IDs for repeated custom pages

Consecutive custom `Page` instances with the default `session_id` can preserve the browser session and update the DOM without rerunning page scripts. Repeated interactive pages should use distinct session IDs or handle PsyNet's `pageUpdated` event explicitly.

*Actions:*

- **PsyNetSkills:** Add a note to the front-end experiment development skill that repeated custom `Page` classes with JavaScript event handlers need unique `session_id` values or `pageUpdated` handling. Confidence: high. Impact: medium. Status: completed. Notes: Added this requirement to `develop-experiment-front-end/SKILL.md`.

## White visual fields should not show frames

For experiments with white image or stimulus backgrounds, a visible frame around
the image area can change the apparent stimulus context. White stimulus fields
should normally blend into the surrounding white page background unless a border
is experimentally intentional.

*Actions:*

- **PsyNetSkills:** Add front-end review guidance that white-background image or stimulus displays should avoid default borders and container frames unless the challenge or experiment design explicitly calls for a frame. Confidence: high. Impact: medium. Status: completed. Notes: Added this requirement to `psychophysics/SKILL.md`.

## Reconsider PsyNet Graphics before custom JavaScript

The evaluator questioned whether custom JavaScript was necessary for this visual
task, because PsyNet Graphics can present images and simple geometric stimuli.
Future plans should explicitly compare PsyNet Graphics against custom
JavaScript for visual experiments before choosing the custom route.

*Actions:*

- **PsyNetSkills:** Expand visual-experiment planning guidance to require an explicit PsyNet Graphics feasibility check before selecting custom JavaScript for image or geometry presentation. Confidence: medium. Impact: medium. Status: completed. Notes: Added this requirement to `develop-experiment-front-end/SKILL.md`.
