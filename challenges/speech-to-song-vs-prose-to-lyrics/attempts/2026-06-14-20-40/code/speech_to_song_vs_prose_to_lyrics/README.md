# Speech-to-song versus prose-to-lyrics

This PsyNet experiment implements a reviewed 3-sentence subset of the
speech-to-song vs. prose-to-lyrics challenge. Each participant completes 15 text
trials and 15 matched audio trials: 3 sentence identities at repetition levels
0-4 in both phases.

Audio stimuli are deterministic local speech assets generated with `espeak-ng`
using voice `en-us`, rate `155`, and pitch `50`. Repeated audio files concatenate
the same base recording with a fixed 350 ms silent pause, so repetition changes
only the number of presentations.

Bots use the same button response path as participants. The text bot uses an
LLM-style text prompt with a deterministic fallback. The audio bot records
`metadata_fallback` because this local environment does not provide an
audio-capable model endpoint.
