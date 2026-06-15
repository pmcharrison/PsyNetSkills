# Learnings

## Put page-level bot responses on `ModularPage`

`RadioButtonControl` did not accept a `bot_response` keyword in the refreshed PsyNet checkout, even though the shared option-control base class handles bot responses internally. The local `bot` demo showed the stable pattern: pass deterministic bot responses to `ModularPage` instead.

*Actions:*
- **PsyNetSkills:** Add a short warning to experiment implementation guidance that control-specific bot response support varies by control, and `ModularPage(bot_response=...)` is the safer pattern for simple page-level responses. Confidence: medium. Impact: low. Status: considering.
## Dashboard basic-data rendering needs JSON-friendly data

Returning Pandas DataFrames from `get_basic_data(context="export")` is useful because PsyNet writes CSV files, but the dashboard `Basic data` tab calls the same method with `context="monitor"` and JSON serializes the result directly. Context-sensitive return values avoided a dashboard-only serialization error while keeping CSV export behavior.

*Actions:*
- **PsyNetSkills:** Mention context-sensitive `get_basic_data` returns in future experiment challenge examples when both dashboard display and CSV export evidence matter. Confidence: medium. Impact: low. Status: considering.
## Pipeline demos can overfit deterministic bot behavior

The evaluation judged the end-to-end pipeline proof strong, but noted that the
scientific demonstration stayed simple because the simulated behavior was
hard-coded and deterministic. Future discovery-oriented attempts should preserve
the same export/analysis evidence while using richer stimulus structure,
less scripted simulated responses, and analysis artifacts that reveal more than
the bot response rule.

*Actions:*
- **PsyNetSkills:** For future discovery-style experiment challenges, encourage attempts to include a richer design or simulation model when doing so does not distract from the required end-to-end evidence. Confidence: medium. Impact: medium. Status: considering.
