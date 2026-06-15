---
title: Cross-cultural Animal Choice Experiment
type: experiment implementation
difficulty: 2
authors: [elif22]
---

## Background

The experiment investigates whether participants from different cultural or language backgrounds make different simple preference judgments about familiar animals. The task should be intentionally brief: each participant completes only two choice trials.

## Stimuli

The stimulus set consists of three animal options: cat, dog, and bird. Each option should be presented with a clear label and a simple visual representation, such as an emoji, icon, or locally bundled image.

The same three animals should appear on every trial. Their order should be randomized independently on each trial to avoid a fixed-position response bias.

## Procedure

Participants first see a short welcome page and brief instructions explaining that they will answer two simple animal-choice questions.

On each trial, participants view the three animal options simultaneously and select one animal. The two trials should use different prompts, for example:

1. "Which animal would you most like to have as a companion?"
2. "Which animal do you think is most respected in your community?"

For each trial, record the prompt, randomized animal order, selected animal, response position, reaction time, participant locale or language setting, and any available cultural-context metadata that can be collected safely without requesting identifying information.

Participants should complete exactly 2 trials, followed by a short thank-you page.

## Implementation details

- Use PsyNet translation-ready participant-facing text so the experiment can be run in multiple languages.
- Keep the interface simple and usable on desktop and mobile screens.
- Allow responses by mouse or touch, and optionally by keyboard shortcuts for the three animal choices.
- Include an analysis script or notebook that summarizes choice proportions by prompt and participant locale or language setting, using exported or simulated data.
