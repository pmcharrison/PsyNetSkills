# Plan

## Science

The experiment will measure simple preferential choices between two multi-feature options. Each trial presents option A and option B with numerical feature values from 0 to 100 and feature validities from 0 to 1. The exported data should let reviewers check whether participants selected one option per trial and whether the recorded choice can be interpreted against the option definitions shown on that trial. Because the study is explicitly cross-cultural, the implementation will keep participant-facing language translatable and will support English, Hindi, and French participant flows.

## Methods

Participants will first see a short welcome page followed by concise task instructions. The instructions will explain that each trial contains two options, that every option has several feature rows, that each row has a value and a validity, and that the participant should choose the option they would prefer.

The main task will contain a fixed manifest of independent choice trials. Each trial will display two cards side by side. Option cards will have fixed numbers of features, specified by the user, for example five rows per option, and every row will display a stable feature label, a value between 0 and 100, and a validity for each feature lying between 0 and 1. The number of features is fixed between option A and option B on the same trial. Participants will respond with a two-button choice, choosing either option A or option B. One response will be saved for each trial.

After the final trial, participants will see a short thank-you page. No real external services, custom credentials, or production recruiter settings will be used. English will be the source locale, with Hindi and French used for local evidence runs.

## Implementation

The experiment will live in `code/decision_making_study/` to avoid importing from a directory named `code`. It will copy the minimal PsyNet support structure needed for local launch checks, including `.gitignore`, `config.txt`, `experiment.py`, and tests where useful.

The round structure is a simple independent repeated-choice design. I will use `StaticNode`, `StaticTrial`, and `StaticTrialMaker` rather than a chain or network architecture, because trial state does not evolve from previous participant responses and no shared node allocation is needed beyond static stimulus assignment.

`experiment.py` will define:

- a language-neutral manifest of trial definitions containing stable feature IDs and numeric values/validities;
- module-level translation setup using `from psynet.utils import get_translator` and `_ = get_translator()`;
- translated welcome, instruction, trial prompt, button labels, and thank-you text;
- a `ChoiceTrial.show_trial` method that renders option cards at participant runtime so translated strings are not serialized into node definitions;
- a `StaticTrialMaker` whose `expected_trials_per_participant` matches the manifest length;
- a bot check that completes all expected trials and asserts one saved answer per trial.

For translation readiness, I will keep `locale` and `supported_locales` together in `config.txt`, with `supported_locales = ["en", "hi", "de"]`. I will avoid f-strings or concatenation inside gettext calls, use `.format(...)` only with uppercase placeholders if placeholders are needed, and keep numeric feature definitions out of translation units. Because challenge attempts must not use real translation credentials, I will create complete Hindi and German `.po` files manually, run PsyNet extraction/consistency checks, and inspect `locales/experiment.pot` for expected strings.

Validation and evidence will include:

- `python experiment.py` from the experiment directory;
- `psynet translate hi de` or the strongest credential-free extraction/consistency command supported by the refreshed PsyNet checkout;
- `psynet test local` with the source locale and, if launch configuration supports it cleanly, repeated local runs for Hindi and French;
- `psynet simulate` with enough bots to produce an example dataset;
- an analysis notebook or script summarizing choices by trial and option features;
- participant-flow screenshots and `participant.mp4` evidence for English, Hindi, and German using the `record-participant-video` skill;
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0` with JSON output under `evidence/`;
- a monitor snapshot and exported `data.zip` under `evidence/`;
- `REPORT.md` summarizing implementation, validation, translation readiness, and any remaining risks.

## Human review

Implementation is paused here for plan review, as required by the PsyNet experiment implementation workflow. Please confirm whether this design is acceptable before coding continues.
