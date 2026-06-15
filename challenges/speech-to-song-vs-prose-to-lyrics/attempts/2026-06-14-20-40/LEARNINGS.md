# Learnings

## Package-relative imports for PsyNet challenge code

`python experiment.py` accepted a sibling import from `generate_audio`, but
`psynet test local` loaded the experiment through Dallinger packaging and needed
the package-relative import path as well.

*Actions:*

- **PsyNetSkills:** Add a note to experiment implementation guidance recommending imports that work both as script execution and packaged Dallinger imports for helper modules in `code/<experiment_slug>/`. Confidence: high. Impact: medium. Status: considering.

## Playwright participant videos are visual evidence only

Playwright's built-in `recordVideo` produced a compact, reproducible
participant-flow MP4 but did not include system audio. Audio-focused attempts
need separate generated-stimulus/export evidence or an ffmpeg system-audio
workflow when audio playback itself must be heard in the video.

*Actions:*

- **PsyNetSkills:** Clarify in the participant recording guidance that Playwright `recordVideo` is acceptable visual evidence only, and audio-sensitive challenge evidence should explicitly pair it with ffmpeg audio capture or documented audio-stimulus/export checks. Confidence: high. Impact: medium. Status: considering.

## Realistic LLM bot simulation for multimodal experiments

The attempt's deterministic bot fallback exercised the PsyNet bot pathway, but
the evaluator wanted more realistic LLM-style simulated data, especially for a
task that compares text and audio judgments. Future attempts need a cleaner
pattern for optional text/audio model calls, mockable local stubs, and export
metadata that distinguishes model-generated responses from deterministic
fallbacks.

*Actions:*

- **PsyNetSkills:** Add guidance for challenge attempts that ask for LLM-style bot data, including how to define optional model-provider hooks, deterministic test stubs, exported `decision_source` metadata, and limitations when no audio-capable model is available. Confidence: high. Impact: high. Status: considering.
- **PsyNet:** Consider a documented helper pattern for PsyNet bots that can call configurable text or audio model adapters while remaining testable without service credentials. Confidence: medium. Impact: medium. Status: considering.
