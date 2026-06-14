---
title: AutoCog-compatible human decision-making task
type: experiment implementation
difficulty: 4
authors: [akjagadish]
---

Implement a self-contained PsyNet experiment generator for a human decision-making
task. The attempt should accept an experiment configuration file containing a
Python dictionary named `config` as input, and should generate a runnable PsyNet
experiment as output. The generated experiment must be prepared for translation
using the Prepare for Translation skill. Provide video evidence showing the
generated experiment running successfully in English, Hindi, and German.

## Participant task

Participants should complete a forced-choice decision task. On each trial, they
should see two options presented side by side. Each option should display the
same fixed set of features, and each feature should have a numerical rating for
option A and option B. The participant should be asked which option they would
choose, and the experiment should save exactly one choice per trial.

The participant flow should include:

- a short welcome page;
- a full instruction page before the experiment starts;
- one choice page per trial, with the two options side by side;
- the core choice instructions repeated on every choice page;
- a short thank-you page after the final trial.

## Configuration format

The generator should read a Python config dictionary with these keys:

- `rationale`: a human-readable explanation of why the design was created. This
  may be preserved in internal metadata or documentation, but it is not needed
  for the participant-facing task.
- `validities`: a list of feature validities, with one value per feature. Each
  validity must be numerical and should be between 0 and 1 inclusive.
- `trial_a_ratings`: a list of rating vectors for option A. Each vector should
  contain one numerical rating per feature.
- `trial_b_ratings`: a list of rating vectors for option B. Each vector should
  contain one numerical rating per feature.
- `max_trials`: the maximum number of trials to include in the task.

The number of features per option should be inferred from the length of
`validities`. Every rating vector in `trial_a_ratings` and `trial_b_ratings`
must match this length. Ratings from `trial_a_ratings` and `trial_b_ratings`
should be paired by list position: the first A vector is paired with the first B
vector, the second A vector with the second B vector, and so on. The generated
trial sequence may swap the screen position of A and B across trials, but it
must preserve the paired relationship between the two rating vectors.

If the number of configured rating pairs is smaller than `max_trials`, repeat
the configured pairs in order until the generated trial list reaches the largest
length that is less than or equal to `max_trials`. Do not create a partial pair.
For example, 10 configured pairs and `max_trials = 50` should produce 50 trials;
10 configured pairs and `max_trials = 54` should still produce 50 trials.

## Example configuration

```python
config = {
    "max_trials": 50,
    "rationale": (
        "This design contrasts Tallying, which counts the number of features "
        "favoring each option, with WADD, which computes a validity-weighted sum."
    ),
    "validities": [0.95, 0.85, 0.6, 0.55, 0.5],
    "trial_a_ratings": [
        [0, 0, 1, 1, 1],
        [1, 1, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 1, 0, 0],
        [0, 1, 0, 1, 0],
        [0, 1, 1, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 1, 1],
        [0, 1, 1, 0, 0],
    ],
    "trial_b_ratings": [
        [1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1],
        [1, 0, 0, 0, 1],
        [0, 1, 1, 1, 0],
        [0, 1, 0, 1, 0],
        [1, 0, 1, 0, 0],
        [1, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 1, 1, 0, 0],
        [1, 0, 0, 1, 1],
    ],
}
```

## Data requirements

For each trial, save the participant's choice and enough metadata to reconstruct
the displayed pair. The saved trial data should include the trial index, the
original paired configuration index, whether presentation order was swapped, the
validities, both option rating vectors, and the selected option. Internal data
keys should remain language-neutral so exported data can be compared across
locales.

## Translation requirements

All participant-facing text must be marked for translation using PsyNet's
translation system. The generated experiment should support English (`en`),
Hindi (`hi`), and German (`de`) without requiring real translation service
credentials. Configuration values used for data reconstruction, such as rating
vectors and validity values, should not be translated. Labels, headings,
instructions, button text, and feature descriptions visible to participants
should be translatable.

## Evidence requirements

The submitted evidence should demonstrate that:

- the generator accepts the example Python config dictionary and produces a
  runnable PsyNet experiment;
- the generated experiment presents two options side by side on each trial;
- each option shows the fixed set of feature ratings and corresponding
  validities;
- option-pair order is preserved even when screen presentation order is swapped;
- one participant choice is saved per trial;
- the welcome, instruction, repeated choice instruction, and thank-you pages are
  present;
- the experiment runs successfully in English, Hindi, and German.

At minimum, provide participant-flow video evidence for English, Hindi, and
German, plus the standard technical evidence expected for PsyNet experiment
implementation challenges.
