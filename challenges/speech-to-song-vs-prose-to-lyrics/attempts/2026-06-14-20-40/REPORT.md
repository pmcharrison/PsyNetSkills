# Report

## Implementation summary

This attempt implements a PsyNet experiment pairing a text-only prose-to-lyrics
phase with a matched auditory speech-to-song phase. Following plan review, the
experiment uses a 3-sentence subset from the 18 public challenge sentences:
`I love you`, `how fast does a Zamboni go?`, and
`I will head to the department store tomorrow`. Each sentence appears at
repetition levels 0-4 in both phases, yielding 15 text trials and 15 audio
trials per participant.

The experiment is implemented in `code/speech_to_song_vs_prose_to_lyrics/`.
It uses PsyNet `StaticNode`, `StaticTrial`, and `StaticTrialMaker` constructs for
the fixed trial grid. The text phase presents repeated transcripts, and the
audio phase presents generated speech assets with identical sentence recordings
concatenated across repetitions.

## Audio generation

Audio assets were generated locally with `espeak-ng` using voice `en-us`, rate
`155`, and pitch `50`. Repetition composites were generated with Python's
standard `wave` library by concatenating the same base utterance with a fixed
350 ms pause. The resulting manifest is stored at
`code/speech_to_song_vs_prose_to_lyrics/data/stimulus_manifest.json`, and the
WAV assets are committed with the attempt.

## Bot and model policy

Bots use the same seven-button response interface as participants. The text bot
constructs an LLM-style prompt from the visible transcript and returns a
deterministic local fallback score. The audio bot records
`metadata_fallback`: the local environment does not provide a waveform-aware
audio model, so audio responses are simulated from sentence and repetition
metadata while still exercising the PsyNet bot pathway.

As an agent, I cannot sit inside a running PsyNet bot prompt and respond
interactively as a live model during `psynet simulate`. I can implement code
paths that call an optional model API or deterministic fallback, and I can use
manual/browser automation outside the bot system to test participant pages.

## Simulation and analysis

`psynet simulate` completed with 6 bots. The export contains 90 text trials and
90 audio trials, matching 6 simulated participants x 15 trials per phase. The
canonical notebook at `evidence/analyses/analysis.ipynb` reads
`evidence/simulated_data.zip`, loads `regular/basic_data/trial.csv`, rescales
ratings to 0-1 transformation scores, computes phase/repetition and
sentence/repetition summaries, correlates text and audio sentence scores, and
plots transformation curves by repetition level.

The simulated data show the expected deterministic fallback pattern:
transformation scores increase with repetition and audio scores are higher than
text scores at larger repetition levels. These results validate the export and
analysis pipeline, not a human behavioral effect.

## Validation status

Completed validation artifacts include:

- generated audio manifest and WAV assets;
- `python experiment.py` entry-point check;
- `psynet test local` bot run through both phases;
- `psynet simulate` export at `evidence/simulated_data.zip`;
- executed notebook at `evidence/analyses/analysis.ipynb`.

Additional participant-flow, monitor, and performance evidence is collected
separately in `evidence/`.
