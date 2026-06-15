---
title: Predicting the Future Across Cultures
type: experiment implementation
difficulty: 5
authors: [raja-marjieh]
---

## Background

Reimplement and extend the everyday prediction task from Griffiths and Tenenbaum (2006), focusing on how people estimate a total duration or extent, `t_total`, from an observed amount so far, `t_past`. The original study asked participants to make intuitive predictions about everyday phenomena whose real-world distributions have different shapes. This challenge narrows the implementation to five categories from the paper's Materials section and extends the participant-facing experiment to English, Italian, and Hebrew using PsyNet's translation pipeline.

The participant experience should feel like a concise survey: participants read short contextual vignettes, receive one observed value, and enter a numerical prediction for the total duration or extent. They should be encouraged to answer from intuition rather than by calculation.

## Required task categories and stimuli

Implement the following five task categories and `t_past` values:

| Category | Prompt basis | `t_past` values |
| --- | --- | --- |
| Life spans | Predict the age at which a man will die, given his current age. | 18, 39, 61, 83, 96 years |
| Lengths of marriages | Predict how long a person's marriage will last, given how long they have already been married. | 1, 3, 7, 11, 23 years |
| Movie run times | Predict the total length of a movie, given how long someone has already been watching it. | 30, 60, 80, 95, 110 minutes |
| Poem lengths | Predict the total number of lines in a poem, given the line number of a quoted favorite line. | 2, 5, 12, 32, 67 lines |
| Waiting times | Predict the total time on hold, given how long someone has already been waiting. | 1, 3, 7, 11, 23 minutes |

For each trial, present a short vignette adapted from the paper's Materials section, one observed `t_past` value, and a numeric response field for the participant's predicted `t_total`. The response validation should reject non-numeric answers and predictions smaller than the presented `t_past`. 

## Design and procedure

Each participant should complete one trial from each of the five categories. Randomize the order of categories for each participant, and randomly assign one of the five `t_past` values within each category. Record the category, vignette identifier, `t_past`, unit, displayed language or locale, numerical prediction, whether the response is finite, reaction time, and any validation failures or retries that are useful for quality control.

The experiment should begin with brief instructions explaining that each question asks for an intuitive prediction from limited information. The task should end with a short debrief noting that the study concerns everyday prediction under uncertainty. Do not ask participants to reveal personally identifying information or to use real service credentials.

## Translation and localization requirements

Follow the `prepare-for-translation` skill. All participant-facing text must be marked for PsyNet internationalization, and the experiment must be demonstrable in:

- English (`en`);
- Italian (`it`);
- Hebrew (`he`), with appropriate right-to-left presentation where needed.

Use stable, language-neutral identifiers in trial definitions, and resolve translated vignettes and labels at render time so that exported data are comparable across languages. Configure PsyNet locale settings for the three requested languages, generate or provide the locale files needed for local testing without production translation credentials, and verify that `locales/experiment.pot` contains the expected participant-facing strings.

## Implementation workflow

Follow the `psynet-experiment-implementation` skill when preparing the attempt. The attempt should include:

1. `PLAN.md`, with scientific motivation, methods, and implementation details.
2. A runnable PsyNet experiment implementing the five task categories.
3. Translation-ready source text and locale configuration for English, Italian, and Hebrew.
4. Evidence that the task can be previewed or tested in all three languages.
5. Simulated participants that exercise the same data paths as real participants.
6. `evidence/simulated_data.zip`, produced from a PsyNet simulation.
7. `evidence/analyses/analysis.ipynb`, executed with outputs embedded.
8. `REPORT.md`, summarizing the implementation, simulation, translation readiness, and any limitations.

## Simulated participants and analysis

Design bot responses to produce plausible numerical predictions while intentionally simulating cross-cultural variation across the three languages. The variation should be modest and documented: for example, bots in different locales may use different offsets or slopes for some categories while preserving the constraint that finite `t_total` is at least `t_past`. The goal is not to claim real cultural differences, but to demonstrate that the experiment and analysis can detect condition-by-language patterns if they are present.

The analysis notebook should load the simulated export and produce a condition-by-language grid figure similar in spirit to Figure 2 of Griffiths and Tenenbaum (2006). Each panel should plot `t_past` on the x-axis and finite predicted `t_total` on the y-axis as a scatter plot, faceted by task category and language. Include enough summary code to make clear how invalid responses and "forever" marriage responses are filtered, encoded, or visualized.

## Reference material

Use the attached Griffiths and Tenenbaum (2006) paper in `references/` as the primary source for the Materials section and for the target style of the analysis figure. Do not invent additional citations, external datasets, or bibliographic details.
