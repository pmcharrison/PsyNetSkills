---
title: Continuous music emotion slider
type: experiment implementation
difficulty: 6
authors: [ww577]
---

Implement a PsyNet experiment inspired by the PsyNet
`demos/pipelines/step_tag` emotion-tagging demo, but replace free-text tags with
continuous emotion ratings. Participants should listen to short audio clips and
rate how the perceived emotion changes over time.

The experiment should run entirely in a local PsyNet development environment. Do
not use real participant recruitment, production credentials, commercial
streaming services, private audio, or copyrighted downloads. Use local PsyNet
demo audio, generated audio, or short placeholder clips committed with the
attempt. Document how a researcher would replace the demonstration stimuli with
real study clips, including the expected stimulus metadata fields.

## Participant experience

Participants complete an introduction explaining that they will hear brief music
or sound clips and continuously report perceived emotion during playback. The
main task should present a manageable set of trials. On each trial:

1. The participant sees clear instructions for the current rating task.
2. The participant starts or hears a short audio clip.
3. During playback, the participant continuously rates at least two emotion
   dimensions, such as valence and arousal, using sliders or another
   time-resolved response control.
4. The interface records a time-stamped trajectory for each dimension, not only
   a single end-of-trial response.
5. The participant can finish the trial only after the required rating window is
   complete.

The participant-facing wording should make clear that the ratings describe the
perceived emotion in the sound, not the participant's own mood. Use simple scale
labels, for example negative to positive for valence and calm to energetic for
arousal.

## Stimuli and sampling

Provide a small local demonstration stimulus set sufficient for local testing
and bot runs. Each stimulus should have a stable identifier, an audio path, and
any relevant condition metadata, such as placeholder condition, excerpt type, or
intended affective category. The experiment should make it straightforward to
replace the demonstration clips with a larger CSV or similar structured metadata
file for a real study.

The implementation may use generated tones, short synthesized clips, or existing
PsyNet demo assets. It must not depend on private or production audio. Any notes
about real stimuli should be framed as replacement instructions rather than as
claims about data already collected.

## Data requirements

Save enough structured data to reconstruct every presented trial. At minimum,
the saved data should link each rating sample to:

- the participant or bot session;
- the trial and stimulus identifier;
- the audio file or stimulus metadata row;
- the emotion dimension being rated;
- the rating value;
- the timestamp or elapsed playback time for that rating sample;
- the condition metadata used for analysis.

Repeated samples at regular intervals are acceptable if true browser-continuous
event capture is impractical, but the attempt should explain the sampling rate or
event policy. The stored trajectories should be suitable for plotting each
dimension over time and averaging trajectories by stimulus.

## Validation, evidence, and analysis

The attempt should include local run instructions and demonstrate that the
experiment runs with PsyNet bots. It should record participant-facing evidence,
such as a browser video or screenshots, showing the continuous-rating task in
use. It should also export data from a local or bot run, or provide clearly
labelled simulated PsyNet-format data when a full export is impractical.

Include an analysis script that reads the exported or simulated PsyNet-format
data and summarizes rating trajectories by stimulus and condition. The analysis
should compute interpretable summaries, such as mean valence and arousal over
time, per-stimulus averages, or simple trajectory plots/tables. If the data come
from bots or simulation, the documentation must state that the outputs validate
the workflow only and do not support real emotion-science conclusions.
