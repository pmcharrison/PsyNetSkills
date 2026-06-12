# Learnings

## Keep repeated per-trial instructions visually lean

Evaluator feedback: the experiment works correctly but looks somewhat bulky.
The choice pages repeat the full instructions in an expandable panel that was
rendered expanded by default, pushing the actual stimulus (the two option
cards) down the page on every trial. When a challenge asks for instructions to
be repeated on the task page, prefer a collapsed-by-default details panel or a
single compact line with an expandable remainder, so the stimulus stays the
visual focus.

*Actions:*

- **PsyNetSkills:** Add a design note to `psynet-experiment-implementation`
  (participant-facing UI guidance): repeated instructions on trial pages
  should default to collapsed/compact so the stimulus dominates the page.
  Confidence: medium. Status: considering.

## Do not store translated text in trial/node definitions

The first implementation put the translated scenario texts (via `_()` at module
scope) directly into `StaticNode` definitions. The instructions pages rendered
in Hindi, but every trial page stayed English: node definitions are serialized
to the database in a context where the translator is inactive, so whatever
string is stored at node-creation time is frozen and locale-dependent. The fix
was to store only a locale-independent `scenario_id` in the node definition and
resolve the translated texts at render time in `show_trial` from a module-level
dictionary (which is evaluated with the active locale in the serving process).
This also makes the exported data locale-independent.

*Actions:*

- **PsyNetSkills:** Add this gotcha to the `prepare-for-translation` skill:
  trial-maker node definitions must store stable keys, with translation applied
  in `show_trial`, not at node-definition time. Confidence: high. Status:
  considering.
- **PsyNet:** Document in the internationalization tutorial that translated
  strings must not be baked into node/trial definitions, or make node-creation
  translation behavior consistent with page rendering. Confidence: medium.
  Status: considering.

## Manual PO files satisfy `psynet translate` without credentials

`psynet translate` only invokes a machine translator for entries that are
missing or fuzzy. Writing complete, non-fuzzy `experiment.po` files by hand
(agent-authored translations) lets the full `psynet translate hi fr` command
and `check_translations` pass with no OpenAI/Google credentials, which fits the
repository credential policy. Launch checks require the `.po` files to exist
for every supported locale, so `psynet test local` fails until they are
created.

*Actions:*

- **PsyNetSkills:** Mention in `prepare-for-translation` that fully translated,
  non-fuzzy PO files make `psynet translate` itself a credential-free
  validation step. Confidence: medium. Status: considering.

## `get_translator()` fails in plain-script smoke tests

`python experiment.py` (recommended in the validation reference) crashes with
`AttributeError: 'NoneType' object has no attribute 'split'` when the module
uses `get_translator()`, because `__package__` is `None` outside the deployment
package. Passing `namespace="experiment"` explicitly fixes the smoke test and
behaves identically in deployment.

*Actions:*

- **PsyNet:** Make `get_translator` fall back gracefully (e.g. to the
  `experiment` namespace or the null translator) when `__package__` is `None`.
  Confidence: medium. Status: considering.

## PsyNet's end-page "Finish" button is not translated

With `locale = hi`/`fr`, the `SuccessfulEndPage` body text is translated, but
its "Finish" push button stays English: `psynet/end.py` uses
`PushButtonControl(["Finish"])`, so the visible label is the untranslated
choice key. The debug-only `HotAirRecruiter` exit page ("You're finished!") is
also English, but that page is not shown to real participants.

*Actions:*

- **PsyNet:** Give the end-page Finish button a translated label
  (e.g. `PushButtonControl(["Finish"], labels=[_("Finish")])`) and add "Finish"
  to PsyNet's own locales. Confidence: high. Status: considering.

## Locale-independent end detection for scripted participant runs

A Playwright runner that detects the end of the experiment by matching English
page text breaks for non-English locales. Detecting the locale-independent
`/recruiter-exit` URL works for all locales. Also note the end page's Finish
button is a single `button.push-button`, so a runner that requires two or more
push buttons for choice pages will deadlock there.

*Actions:*

- **PsyNetSkills:** Note URL-based completion detection in the
  `record-participant-video` or attempt-evidence references for multilingual
  recordings. Confidence: medium. Status: considering.

## Config keys must live in exactly one place

Defining `supported_locales` in both the experiment class `config` dict and
`config.txt` aborts launch with "Config variable supported_locales was
registered both in config.txt and experiment.py". Keeping `locale` and
`supported_locales` together in `config.txt` makes locale switching for
per-language evidence runs a one-line edit.

*Actions:*

- **PsyNetSkills:** Recommend in `prepare-for-translation` that `locale` and
  `supported_locales` live together in `config.txt` (not the experiment class
  config) so evidence runs can switch language with a one-line edit.
  Confidence: low. Status: considering.
