# Learnings

## Include standard PsyNet experiment support files

`psynet test local` failed until the attempt included both a local `config.txt`
with required Dallinger metadata and a standard experiment-level `test.py`.

*Actions:*

- **PsyNetSkills:** Update the attempt-challenge guidance for runnable PsyNet experiments to list `config.txt` and `test.py` alongside `.gitignore` as standard support files to copy or create before local validation. Confidence: high. Impact: low. Status: considering.
## Use accelerated participant recordings for complete long flows

The full text-heavy participant flow could not be shown clearly under three
minutes at normal interaction speed. Recording a longer raw MP4 and publishing a
2x accelerated copy kept the complete flow reviewable and within the evidence
limit.

*Actions:*

- **PsyNetSkills:** Add a short example to the `record-participant-video` skill showing how to record a longer raw run, speed it up with `setpts`, verify the accelerated copy, and remove the raw file before committing. Confidence: medium. Impact: medium. Status: considering.
## Validate probe and profile realism separately from kit mechanics

The attempt demonstrates the mechanics of ECLAIR-style probes and LLM-assisted
profile flagging, but the evaluator noted that richer response distributions
would be needed before treating those probes and profile fixtures as calibrated
research instruments.

*Actions:*

- **PsyNetSkills:** For future AI-assistance review challenges, distinguish implementation-mechanics evidence from validation evidence for ECLAIR-style probes and LLM-assisted profile fixtures, and ask for richer real or experimentally controlled response distributions when calibration is part of the challenge goal. Confidence: high. Impact: high. Status: considering.
