---
title: Open-ended STEP tagging experiment
type: experiment implementation
difficulty: 7
authors: [elif22]
---

Implement a PsyNet experiment that collects open-ended emotion tags for short
music clips using a STEP-like iterative tagging procedure.

The experiment should be designed for a cross-cultural music-emotion study, but
it should run locally with a small replaceable stimulus set. Do not depend on
commercial streaming APIs, real recruitment credentials, or copyrighted music
downloads. Instead, include or generate a minimal local set of short audio
stimuli for testing, and make the stimulus metadata easy to replace with a CSV or
similar structured file containing clip identifiers, culture labels, and audio
paths.

## Participant experience

Participants complete a consent/introduction page explaining that they will
listen to short music clips and describe the emotions or affective qualities they
hear in the music. The study should then present a sequence of music trials. On
each trial:

1. The participant listens to one 15-second music clip.
2. The participant may enter one or more new single-word tags describing the
   emotional or affective character of the clip.
3. If tags from previous participants are available for that clip, the
   participant rates how well each existing tag applies to the clip.
4. The participant can flag existing tags that are inappropriate, irrelevant,
   misspelled beyond recognition, genre labels, direct lyrics, or otherwise not
   valid emotion or affect descriptors.

The tagging interface should encourage native-language responses and should make
the constraints clear: tags should be single words, should not be genre labels,
should not quote lyrics, and should be no longer than 15 characters. Multiple
new tags are allowed per clip. A participant should annotate a manageable subset
of clips, with a default target of 15 clips per participant when enough stimuli
are available.

## Iterative STEP behavior

The implementation should maintain a per-stimulus pool of tags that evolves as
participants complete trials. Early participants may see no existing tags for a
clip; later participants should see tags contributed by previous participants.
For each stimulus, the experiment should support at least five participant
passes or iterations in the sense that tags can be generated, rated, and flagged
over repeated exposures by independent participants.

Store enough data to reconstruct, for each stimulus:

- new tags submitted by each participant;
- ratings of existing tags;
- flags and reasons, if reasons are collected;
- the iteration or exposure order in which each contribution occurred.

The resulting data should be suitable for computing a weighted bag-of-words
representation per clip, where tag weights can reflect participant ratings and
where flagged tags can be excluded or reviewed.

## Stimulus sampling

The design should support balanced music sampling by culture. For a full study,
each target country would receive a mixture of songs from its own culture and
from other cultures, with 15-second excerpts. For the implementation challenge,
provide a small local demonstration set that includes at least three culture
labels and shows how the experiment would sample a balanced subset of clips for
each participant.

## Output and documentation

Document how to run the experiment locally, how to replace the demonstration
stimuli with real study stimuli, and where the collected tags, ratings, and
flags are stored. Include a brief explanation of how the saved data would feed a
later tag-cleaning and emotionality-selection stage, but do not implement the
separate dense-rating experiment.
