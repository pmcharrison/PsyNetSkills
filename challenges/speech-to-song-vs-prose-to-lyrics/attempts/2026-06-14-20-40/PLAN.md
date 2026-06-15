# Plan

## Science

The experiment will test whether repetition increases perceived song-likeness in
two matched modalities: a text-only prose-to-lyrics judgment and an auditory
speech-to-song analogue. The central comparison will be the transformation score
for the same sentence identities and repetition levels in the text and audio
phases. Scores will be collected on the requested 0-6 speech-to-song scale and
rescaled to 0-1 for analysis.

## Methods

The study uses a within-participant, two-phase design. Every participant first
completes the text phase and then the audio phase, matching the public challenge
instructions. Both phases use the same reviewed subset of three sentence
identities and the same five repetition levels, 0-4, where level 0 is one
presentation and level 4 is five presentations. The main independent variables
are `phase`, `sentence_id`, and `repetition_level`; the main dependent measure
is the participant's 0-6 speech-to-song rating.

The materials are a 3-sentence subset selected from the challenge list to keep
the local implementation and review tractable: one short phrase, one question,
and one longer sentence. Text trials will display the transcript formed by
repeating the sentence `repetition_level + 1` times. Audio trials will use
locally generated speech recordings for the base sentences. For repeated audio
items, the experiment will generate or bundle composite audio files by
concatenating the identical base recording with a fixed silent pause between
presentations. This keeps the acoustic token constant for a given sentence and
changes only the number of presentations.

The procedure begins with consent and task instructions, followed by the text
phase, a short transition page, the audio phase, and a closing page. Each phase
administers the complete 3 x 5 reviewed subset, yielding 15 text trials and 15
audio trials per participant. Trial order will be randomized within each phase
by PsyNet while preserving explicit metadata for sentence identity, sentence
text, repetition level, phase, transcript, asset path, and trial position. This
subset-grid strategy keeps the two phases directly comparable without
overloading local validation.

On text trials, participants read the transcript and judge whether the original
audio is more likely to have been speech or song. On audio trials, participants
hear the repeated spoken sentence, are told that repeated presentations are
intentionally identical, and then make the same judgment. The response scale will
use seven labeled choices from 0 (`Definitely speech`) to 6 (`Definitely song`).
The exported trial records will preserve the raw response, response time from
PsyNet's trial machinery, phase, sentence ID, sentence text, repetition level,
presented transcript, and order metadata.

## Implementation

The experiment will live in `code/speech_to_song_vs_prose_to_lyrics/` so the
attempt is self-contained and avoids a top-level package named `code`. It will
start from PsyNet's static-trial and simple audio-rating patterns:

- `StaticNode`, `StaticTrial`, and `StaticTrialMaker` will represent the fixed
  sentence/repetition trials.
- Two trial makers, `text_trials` and `audio_trials`, will enforce the required
  phase order while using matched node metadata.
- `ModularPage` plus a push-button or keyboard-compatible seven-choice control
  will collect 0-6 ratings.
- `AudioPrompt` will present audio assets and enable submission only after the
  prompt has ended.
- `InfoPage`, `MainConsent`, and `Timeline` will assemble the participant flow.

Stimulus generation will be deterministic and local. I will add a small asset
generation script that tries an installed command-line speech synthesizer such
as `espeak-ng` or `espeak` and records the exact command and voice settings in
the attempt documentation. If no suitable synthesizer is available, the blocker
will be recorded rather than substituting non-speech audio as if it were valid
speech. Repetition composites will be generated with Python's `wave` tooling or
another local deterministic audio utility, using a fixed silence duration.

Trial definitions will be built from constants in `experiment.py`, including
sentence IDs for the three reviewed sentences, the original sentence text,
repetition level, full transcript, phase, and expected audio asset names. The
audio nodes will attach cached PsyNet assets for the generated WAV files. The
text nodes will not attach external assets but will use the same
sentence/repetition metadata.

Bots will exercise the same page controls used by participants. The text bot
will build an LLM-style prompt that mirrors the human text instructions and asks
for an integer 0-6 score based only on the transcript. The audio bot pathway
will prefer an optional audio-capable provider only if environment variables are
present; in the clean local environment it will use a documented fallback score
derived from sentence/repetition metadata and will record that the decision came
from metadata rather than waveform analysis. No API keys or production
credentials will be committed.

The analysis notebook will be saved as
`evidence/analyses/analysis.ipynb`. It will read the simulated PsyNet export
directly, extract trial-level ratings for both phases, rescale ratings to 0-1,
compute sentence x repetition means, correlate text and audio sentence scores,
plot mean transformation score by repetition and phase with uncertainty
intervals, and include sentence-level tables or compact plots. The notebook will
state that the demonstrated analysis uses local bot/simulated data unless a real
local participant export is produced during validation.

Validation and evidence collection after plan approval will follow the
experiment implementation checklist:

- run `python experiment.py` from the experiment directory to verify stimulus
  discovery/generation;
- run `psynet test local`;
- run `psynet simulate` with enough bots to produce a useful export at
  `evidence/simulated_data.zip`;
- execute the canonical notebook in place after installing notebook tooling into
  the PsyNet virtualenv;
- run the functional/performance checks from the validation reference, recording
  blockers clearly if the local PsyNet services cannot support a check;
- collect participant-flow screenshots/video with the participant recording
  workflow;
- write `REPORT.md` summarizing implementation choices, audio synthesis,
  bot/model limitations, validation, simulation, and analysis results.

## Human review outcome

- Use a subset of 3 sentences rather than all 18.
- Record `raja-marjieh` as the human author.
- No specific text-to-speech voice or synthesizer is preferred; use the first
  suitable deterministic local tool available and document it.
