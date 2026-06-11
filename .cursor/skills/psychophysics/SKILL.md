---
name: psychophysics
description: Design and validate PsyNet psychophysics experiments with controlled stimuli, timing, prescreeners, and analyzable trial metadata.
authors: [raja-marjieh]
---

# Implement psychophysics experiments

Use this skill when creating or revising PsyNet experiments that measure perceptual judgments, discrimination, detection, identification, similarity, memory, thresholds, or response times.

## Required reads

- Read `psynet-experiment-implementation/SKILL.md` for the general PsyNet implementation workflow, demo-first development, and validation expectations.
- For challenge attempts, read `attempt-challenge/SKILL.md` and its evidence references before collecting review artifacts.
- Inspect the closest PsyNet demos and framework APIs for the relevant modality before adding custom frontend code.

## Design principles

1. Represent trials as data. Use `StaticNode`/`StaticTrialMaker` or another PsyNet trial-maker abstraction so stimulus identity, parameters, block, timing, and correctness metadata live in node definitions rather than ad hoc browser state.
2. Use PsyNet-native stimulus presentation. Prefer `GraphicPrompt`, native graphics frames, controls, events, and trial makers over custom JavaScript for fixation, stimulus display, delays, and response activation.
3. Begin timed visual trials with a fixation cross. Keep the fixation centered, keep subsequent stimuli centered around it when the task uses central attention, and document any intentional eccentricity or spatial layout.
4. Fix and record timing. Define presentation and delay durations as constants, keep them consistent within a task unless adaptivity is part of the design, and record the values in trial metadata. Delays used for memory or retention should normally be at least 500 ms unless the specification says otherwise.
5. Store enough metadata to reconstruct every trial. Include stimulus IDs, perceptual dimensions, display positions, block labels, trial condition, correct answer or scoring target, participant response, accuracy, and reaction time.
6. Document sampling and balancing. State how stimulus pairs, set sizes, positions, target-present trials, lures, repeats, or adaptive staircases are chosen. Use deterministic manifests when the stimulus space is nontrivial.
7. Include modality-appropriate prescreeners. Use PsyNet's Ishihara-style `ColorBlindnessTest` for color-critical tasks; use PsyNet volume, headphone, hearing, or audio checks when sound perception matters; add comprehension or practice checks for unfamiliar tasks. Decide explicitly whether each prescreener should exclude participants, stratify them, or serve only as a post hoc covariate.
8. Keep response paths comparable. Ensure bot responses, formatted answers, and scoring use the same response representation as the participant-facing path.
9. Analyze at the trial level. Provide analysis code that can consume exported data or a documented simulated dataset and summarize psychophysical outcomes such as accuracy, confusion probabilities, thresholds, similarity matrices, and reaction-time distributions.

## Validation

- Run `python experiment.py` or an equivalent construction check to verify stimulus manifests and node counts.
- Run `psynet test local` for PsyNet experiments, using a short documented profile only for visual review when the full design is long.
- Inspect participant-facing pages in a browser or recording for fixation placement, stimulus centering, labels, endpoint text, button states, and escaped HTML.
- Keep visual evidence profiles representative but short. Prefer direct short recordings over long raw recordings that need expensive multi-segment editing.
- For challenge attempts, collect participant video, exported data, monitor, and performance evidence according to the attempt evidence references.

## Common failures

- Do not draw timed psychophysics stimuli with one-off HTML or custom JavaScript when PsyNet graphics frames can express the timing and layout.
- Do not leave fixation crosses drifting relative to the stimulus display; small coordinate mistakes can change the task.
- Do not use color as a primary dimension without a color-vision check unless the prompt explicitly excludes screening; do not let that check exclude participants when the study only needs to record color-vision status.
- Do not record only labels such as `"trial 3"`; reviewers must be able to reconstruct the actual stimuli and conditions.
- Do not let minimal review profiles replace the canonical experiment design. Keep them documented as evidence-generation aids.
