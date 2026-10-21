# Cross-cultural decision making

A PsyNet experiment in which the participant chooses between two options
presented side by side. Each option is described by a variable number of
features (2-5). One choice is saved per trial.

## Structure

- Welcome page, then full instructions.
- Six choice trials (`StaticTrialMaker`); each trial shows the two options as
  side-by-side cards, repeats the full instructions in an expandable panel,
  and records the chosen option (`option_1` / `option_2`).
- Thank-you page, then the standard PsyNet end page.

## Translation

The experiment is prepared for translation with `psynet translate`. All
participant-facing strings are marked with `_()` from
`psynet.utils.get_translator`. Translations live in
`locales/<locale>/LC_MESSAGES/experiment.po` (Hindi `hi` and French `fr` are
included; they were translated manually because no machine-translation
credentials are used in this workshop environment).

Select the language by setting `locale` in `config.txt` (`en`, `hi`, or `fr`)
and relaunching the experiment.

## Running

```bash
psynet test local    # automated bot test
psynet debug local   # interactive debugging
```
