# Learnings

## Gibbs demos need capacity checks when increasing bot counts

The original Gibbs demo completed six bots but depleted available Gibbs nodes before ten bots could each complete the expected four normal trials plus three repeats. Increasing simulated participant counts can require revisiting `max_nodes_per_chain`, `trials_per_node`, or related trial-maker capacity settings even when the participant-facing task is unchanged.

*Actions:*
- **PsyNetSkills:** Update challenge or simulation guidance to remind agents to calculate Gibbs trial capacity before increasing `test_n_bots`. Confidence: high. Impact: medium. Status: considering.

## Analysis notebooks should stay small and read committed exports directly

The canonical notebook stayed well under the dashboard truncation limit by using one low-DPI plot and reading `evidence/simulated_data.zip` directly rather than embedding large derived artifacts.

*Actions:*
- **PsyNetSkills:** Keep the existing experiment evidence guidance about low-DPI executed notebooks and direct CSV-reading code; it worked well for this attempt. Confidence: medium. Impact: low. Status: considering.
