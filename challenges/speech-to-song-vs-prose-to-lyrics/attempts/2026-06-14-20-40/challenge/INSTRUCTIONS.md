---
title: Speech-to-song vs. prose-to-lyrics
type: experiment implementation
difficulty: 8
authors: [raja-marjieh]
---

Implement a PsyNet experiment that pairs the text-based prose-to-lyrics
paradigm from Marjieh et al. (2024) with a matched auditory speech-to-song
block using the same sentence materials.

The experiment should use two within-participant phases. In the first phase,
participants complete the textual prose-to-lyrics task. In the second phase,
participants complete an auditory version that follows the logic of the
speech-to-song illusion while paralleling the text phase as closely as possible.
Both phases should use the same sentence identities and the same repetition
levels, so that sentence-level transformation scores can be compared across
modalities.

## Stimuli

Use the following 18 sentences from the Behavioral Methods section of Marjieh
et al. (2024):

1. `I love you`
2. `I get it`
3. `I want you`
4. `stay back`
5. `stay still`
6. `go away`
7. `take it back`
8. `I need time`
9. `how fast does a Zamboni go?`
10. `but once in a while you step on it from one end to the other`
11. `if it takes an extra minute to do it, that's fine`
12. `and wait 10 seconds or so between each bounce`
13. `I drilled a hole through the top of my rack`
14. `what kind of car would it be?`
15. `I grew up watching them`
16. `it has really kept us growing`
17. `sometimes behave so strangely`
18. `I will head to the department store tomorrow`

Each sentence should be presented at repetition levels 0, 1, 2, 3, and 4. Treat
level 0 as a single presentation of the sentence. For repeated text items,
construct the transcript by concatenating the sentence the corresponding number
of additional times. For repeated audio items, play the same spoken sentence
recording the corresponding number of additional times, with a short,
consistent pause between presentations.

If suitable recordings of the 18 sentences are not provided, generate local
audio stimuli from the text using a deterministic text-to-speech or synthesis
pipeline and document the method. The auditory block should keep the acoustic
content identical across repetitions for a given sentence, changing only the
number of presentations.

## Text phase: prose-to-lyrics

The text phase should follow the paper's behavioral task. On each trial, show a
text transcript and ask participants to judge whether the original audio is more
likely to have been speech or song based on the transcript alone.

Use a seven-point response scale from 0 to 6, where 0 means definitely speech
and 6 means definitely song. Store enough trial data to recover the participant
identifier, phase, sentence identifier, sentence text, repetition level, full
presented transcript, response, response time, and any trial-order metadata.

The full 18 x 5 item set may be sampled per participant, as in the paper, or
administered in full if that is more convenient for local testing. The sampling
or blocking strategy should be documented and should avoid systematic
confounding of sentence, repetition level, and phase order.

## Audio phase: speech-to-song analogue

The auditory phase should use the same rating scale and sentence/repetition
structure as the text phase. On each trial, participants should hear the spoken
sentence one or more times and then judge whether the recording sounds more
like speech or song.

Design this block according to standard PsyNet principles: use PsyNet's audio
trial/page patterns where appropriate, preload or generate assets reliably, keep
stimulus metadata explicit, and make the trial data exportable without relying
on hidden browser state. The task should make clear that the repeated audio
presentations are intentionally identical.

The two phases should be arranged so their data can be compared directly. For
example, use shared sentence IDs, shared repetition-level labels, matched rating
scales, and clear phase labels such as `text` and `audio`.

## Bots and AI simulation

Implement local bots or simulated participants that can complete both phases.
Where possible, bots should call an LLM-style decision agent to produce
speech-versus-song scores from the stimulus shown to the participant.

For the text phase, the AI prompt should closely match the human instructions
and should ask for a numeric speech-to-song score derived only from the
presented transcript. For the audio phase, prefer an audio-capable model or
agent interface that receives the audio stimulus itself. If the local
environment does not provide a usable audio model, implement a documented,
mockable fallback that still exercises the same PsyNet bot pathway and clearly
records that the audio decision was simulated from text or metadata rather than
from the waveform.

Do not commit real API keys, production credentials, paid recruitment settings,
or service-specific secrets. Any external model integration should be optional,
configured through environment variables, and covered by local tests or stubs so
the experiment can run in a clean development environment.

## Analysis notebook

Add a Jupyter notebook that analyzes exported or simulated PsyNet-format data
from both phases. The notebook should:

- load the trial-level ratings from both phases;
- rescale the 0-6 ratings to a 0-1 transformation score;
- compute sentence-level mean scores by phase and repetition level;
- correlate text-phase and audio-phase sentence scores across repetition levels;
- plot the average transformation score as a function of repetition for each
  phase, with uncertainty intervals where the data support them;
- include sentence-level plots or tables showing which sentences transform more
  strongly under repetition; and
- state clearly whether the demonstrated analysis uses real local run data,
  PsyNet bots, or simulated data.

The plots should be visually comparable to the repetition curves in Marjieh et
al. (2024), especially the average transformation score by repetition level and
the sentence-level transformation profiles.

## Evidence and documentation

The completed attempt should include:

- a working PsyNet experiment with both phases;
- locally generated or bundled audio assets, plus documentation of how they were
  produced;
- local test evidence showing that the experiment runs and records data for both
  phases;
- bot or simulated-participant evidence for both text and audio trials;
- an exported or simulated dataset suitable for the notebook;
- the completed analysis notebook and rendered plots; and
- a short report explaining implementation choices, any audio-model or LLM
  limitations, and how the result maps onto the behavioral paradigm in the
  reference paper.
