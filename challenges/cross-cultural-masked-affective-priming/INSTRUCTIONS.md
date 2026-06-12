---
title: Cross-cultural masked affective priming
type: experiment implementation
difficulty: 7
authors: [elif22]
---

Implement a PsyNet experiment in which participants classify ambiguous facial
expressions after briefly presented emotional primes. The task should follow the
logic of masked affective priming: a fixation display is followed by a forward
mask, a very brief emotional prime, a backward mask, and then an ambiguous target
face that the participant must classify. The implementation should be suitable
for local testing and should not require real participant recruitment, production
credentials, private face databases, or copyrighted stimulus downloads.

## Participant experience

Participants first read a short introduction explaining that they will see rapid
visual displays and then classify the expression on a target face. The
instructions should emphasize the classification task rather than inviting
participants to look for primes. Participants should complete a small number of
practice trials before the main block.

On each trial, the participant should experience the following sequence:

1. A fixation cross or similar attentional cue.
2. A forward mask shown briefly before the prime.
3. An emotional prime face or face-like image shown very briefly, short enough
   to be treated as masked in a local demonstration.
4. A backward mask.
5. An ambiguous target face that remains visible until the participant responds.
6. A forced-choice expression classification, for example happy versus angry or
   positive versus negative.
7. A short inter-trial interval before the next trial.

The timings should be defined in one place and documented in the attempt, with
separate fields for fixation, forward mask, prime, backward mask, target display,
and inter-trial interval. Exact laboratory-grade timing is not required for the
local PsyNet demonstration, but the code should preserve the intended sequence
and make the timing assumptions transparent.

## Stimuli and cultural design

Provide a small local demonstration stimulus set with structured metadata. The
stimuli may be generated placeholders, synthetic face-like images, or other
clearly reusable assets committed with the attempt. Do not download or embed
restricted facial-expression datasets. If the implementation uses placeholders,
document how a researcher would replace them with validated stimulus sets.

The stimulus metadata should distinguish at least:

- prime identifier;
- prime affect category;
- prime cultural group or source population label;
- target identifier;
- target ambiguity level or morph label;
- target cultural group or source population label;
- mask identifier;
- congruency condition, such as prime affect matching or mismatching the target
  response category.

The design should include multiple cultural or source-population labels in the
metadata so that the workflow can support cross-cultural analysis. A real study
might compare in-group and out-group primes or targets, but the local
demonstration must label these as demonstration conditions rather than making
claims about real cultural populations.

## Data requirements

Save enough structured data to reconstruct the sequence and condition for every
trial. At minimum, each response record should include:

- participant or bot session identifier;
- trial index;
- prime, mask, and target identifiers;
- prime affect category;
- prime and target cultural group labels;
- target ambiguity level;
- congruency condition;
- intended timing values for each trial phase;
- selected classification response;
- response time measured from target onset when practical;
- whether the response was correct under the demonstration coding.

The experiment should make it possible to analyze whether affect-congruent primes
shift classification of ambiguous targets relative to affect-incongruent primes,
and whether this pattern differs by cultural condition. If the attempt includes
only bot or simulated data, the documentation must state that the results
validate the workflow only and do not support scientific conclusions.

## Validation, evidence, and analysis

The attempt should include local run instructions and demonstrate that the
experiment can run in a PsyNet development environment. Provide participant-
facing evidence, such as a browser video or screenshots, showing the masked trial
sequence and the classification interface. Also provide a bot run, local export,
or clearly labelled simulated PsyNet-format data showing the recorded trial
fields.

Include a short analysis script or notebook that reads the exported or simulated
data and summarizes classification responses by prime affect, target category,
congruency, and cultural condition. The analysis should compute interpretable
priming summaries, such as response proportions and mean response times by
condition, and should clearly separate methodological validation from real
cross-cultural affective-priming inference.
