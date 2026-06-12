# Plan

This plan pauses the attempt before implementation, as required for experiment
implementation challenges.

## Source basis

- Public challenge instructions: `challenge/INSTRUCTIONS.md`.
- Challenge reference note: `challenge/references/notes.md`.
- Target paper: Lahdelma, I., & Eerola, T. (2016). "Single chords convey distinct emotional qualities to both naive and expert listeners." The accessible JYX accepted version is used for method details.
- Supplementary public sources: Uppsala 15-item scale resource page, Watson et al. (1988) PANAS source, public OMSI summaries, and current PsyNet demos/API files in `~/PsyNet`.

## Science

The replication will test whether isolated vertical harmony conveys distinct
perceived emotional qualities without a melodic or harmonic context. The primary
participant-level question is whether the 28 chord-timbre stimuli reproduce the
paper's broad patterns: major triads rated high in valence and happiness/joy,
diminished and augmented triads rated high in tension and low in valence, minor
triads and seventh chords rated higher in nostalgia/longing, and string timbre
raising nostalgia/longing, melancholy/sadness, and tenderness.

The implementation will treat ratings as perceived emotion, not induced emotion,
following the paper's distinction between recognizing expression in music and
personally feeling the emotion. Musical sophistication, nationality, gender, age,
education, and current mood will be measured as background variables, with OMSI
used to form the same four sophistication bands when possible: lower
non-musicians, higher non-musicians, lower musicians, and higher musicians.

## Methods

### Design

The core design is a within-participant rating experiment. Each participant hears
28 isolated chord stimuli: 14 C-root chord forms crossed with two timbres. The
chord factor will be represented at both the detailed stimulus level and the
collapsed chord-type level used in the paper's ANOVAs.

The 14 chord forms will be:

- C major triad: root, first inversion, second inversion.
- C minor triad: root, first inversion, second inversion.
- C diminished triad: root only.
- C augmented triad: root only.
- C dominant seventh: root and third inversion.
- C minor seventh: root and third inversion.
- C major seventh: root and third inversion.

The two timbres will be piano and strings. The original commercial Pro
Tools/Ivory and Vienna Symphonic Library sounds will be reconstructed locally
with PsyNet/JSSynth. Piano will use `InstrumentTimbre("piano")`; strings will
use the closest built-in sustaining string proxy, expected to be
`InstrumentTimbre("violin")`, documented as a deviation from a chamber string
section.

### Materials

Stimulus metadata will be centralized in a `stimuli.py` module. Each stimulus
record will include:

- stable stimulus id;
- chord symbol and chord family;
- inversion label;
- timbre label;
- MIDI pitches, with C4/middle C as root in equal temperament;
- duration, fixed at 4.0 seconds;
- synthesis timbre and any amplitude, envelope, or reverb proxy settings;
- reconstruction notes describing deviations from the source paper.

The rating page will use the paper's nine dimensions. The first three will be
bipolar 1-5 scales:

- valence: negative to positive;
- tension: relaxed to tense;
- energy: low to high.

The remaining six will be unipolar 1-5 scales:

- nostalgia/longing;
- melancholy/sadness;
- interest/expectancy;
- happiness/joy;
- tenderness;
- liking/preference.

The rating descriptions will follow the paper appendix: for example, valence asks
whether the chord conveys positive or negative feelings, tension asks whether it
is calm/relaxed or tense/agitated, and liking/preference is explicitly described
as subjective.

Background questionnaires will include:

- demographic fields: age, gender, nationality, and education;
- PANAS mood questionnaire using the 1-5 labels reported in the paper. The
  visible paper text states that five positive and five negative adjectives were
  used, but does not name the exact subset; the implementation will use a
  documented 10-item subset derived from the Watson et al. PANAS source and mark
  this as a reconstruction choice;
- OMSI-style musical sophistication form. The implementation will capture the
  public ten-factor content reported in later OMSI summaries, derive a 0-1000
  score proxy, and retain the raw item values so the scoring rule is auditable.

### Procedure

The participant flow will be:

1. Consent and browser/audio readiness information.
2. Demographic questions, with required responses.
3. PANAS mood questionnaire.
4. OMSI musical sophistication questionnaire.
5. Chord-rating instructions matching the paper's wording in substance:
   participants should listen to each chord as many times as they like, rate the
   emotional connotations the chord seems to convey, and treat each chord as a
   separate entity.
6. Twenty-eight static rating trials in a randomized order, one per
   chord-timbre stimulus.
7. Completion page.

Each trial will play a 4.0-second JSSynth chord, expose replay controls, prevent
submission before the first playback ends, and then collect the nine ratings on
the same page. All answers will be required before moving on.

## Implementation

The runnable experiment will live under `code/single_chord_emotion/` rather than
directly in `code/`, avoiding a Python package-name collision with the standard
library `code` module.

Planned files:

- `experiment.py`: PsyNet experiment, timeline, questionnaires, static trial
  maker, and bot responses.
- `stimuli.py`: chord definitions, JSSynth sequence construction, timbre
  selection, and metadata export helpers.
- `questionnaires.py`: demographic, PANAS, and OMSI pages.
- `analysis/simulate_data.py`: standalone simulated-data generator with
  participant metadata, questionnaire values, randomized trial rows, and signal
  approximating the target paper's qualitative effects.
- `analysis/extract_features.py`: metadata-based stimulus feature table,
  including pitch/register summaries, interval class counts, simple dissonance
  or roughness proxies, spacing irregularity, and synthesis constants.
- `analysis/chord_emotion_replication.ipynb`: notebook that loads simulated or
  exported data, creates aggregate plots, runs reliability checks, repeated
  measures analyses, background-variable checks, and feature-rating correlations.
- `README.md`: methods note with source citations, reconstruction rationale,
  local run commands, analysis commands, deviations, and evidence instructions.
- `requirements.txt` or project-local metadata only if the implementation needs
  extra analysis dependencies not already available through PsyNet/PsyNetSkills.

The PsyNet structure will follow the `simple_audio_rating` demo:

- `StaticNode` definitions will hold each stimulus and its metadata.
- A custom `StaticTrial` subclass will render a `ModularPage` using `JSSynth`
  as the prompt and `MultiRatingControl` with nine `RatingScale` objects.
- A `StaticTrialMaker` will present all 28 nodes once per participant in a
  participant-specific random order.
- Bot responses will be deterministic enough to exercise all pages and produce
  complete simulated exports, while the standalone simulator will generate
  larger datasets for analysis demonstration.

Data audit fields will include participant id, trial id, stimulus id, chord
family, chord symbol, inversion, timbre, MIDI pitches, duration, synthesis
parameters, trial order, all nine ratings, questionnaire values, computed PANAS
positive/negative scores, computed OMSI proxy score, and musical sophistication
band.

Validation after plan approval will follow the repository evidence checklist:

- run `python experiment.py` from the experiment directory to list or validate
  stimulus definitions;
- run `psynet test local`;
- run `psynet simulate` or the experiment's bot flow to generate exported data;
- run the standalone simulated-data and analysis workflow;
- run `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0` with JSON output under `evidence/`;
- collect participant-flow screenshots and `participant.mp4` using the
  `record-participant-video` skill;
- export `data.zip` and save a monitor snapshot under `evidence/`.

Risks to review before coding:

- The exact original PANAS 10-adjective subset is not named in the visible
  accepted paper text. The implementation should either locate a stronger public
  source before coding or explicitly document the substituted PANAS subset.
- OMSI scoring details may require a proxy if the original scoring instrument is
  not fully public. Raw OMSI responses and the proxy formula must be preserved.
- JSSynth's built-in violin timbre is an approximation to a chamber string
  section with reverb; this deviation should be audible, documented, and carried
  into analysis metadata.
- PsyNet/JSSynth may not log replay counts by default. The minimum faithful
  behavior is unlimited replay; if practical, implementation should add replay
  click logging without destabilizing the standard trial flow.
