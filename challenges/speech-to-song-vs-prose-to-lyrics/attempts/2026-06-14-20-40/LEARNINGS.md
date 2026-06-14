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
