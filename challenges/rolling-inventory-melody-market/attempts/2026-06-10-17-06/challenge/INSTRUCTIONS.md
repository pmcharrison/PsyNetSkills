---
title: Rolling inventory melody market
type: experiment implementation
difficulty: 9
authors: [lucasgautheron]
---

Implement a PsyNet experiment that replicates the rolling-inventory cultural
market paradigm from the Computational Audition Lab `niche-lucas` repository
(`rolling-inventory-replication` branch), but with melodies as the artefact
domain instead of binary grid drawings.

The new experiment should preserve the original's participant flow, network
logic, rolling inventory behaviour, condition structure, timing, validation,
and core data-recording conventions. Only the adoption and creation interfaces,
the market previews, participant-facing wording, and audio-specific screening
should change to suit music creation. Do not carry over the original
experiment's mouse movement or stroke event tracking features.

## Procedure

Participants should complete informed consent and brief instructions explaining
that they will compose short melodies that compete on a shared market. Before
participants enter the main task, include a short audio pre-screening step that
plays a static sound clip containing a human voice saying "five". Participants
must prove that they can hear the clip by typing what was said. Accept the
answer if it is `five` or `5`, ignoring letter case and leading or trailing
whitespace. Participants who cannot pass the audio check should not continue
into the market task.

Each round should consist of two steps:

1. **Adoption step.** When the market already contains items, participants
   browse the current inventory and select one melody to build on. When the
   market is still empty, participants should skip selection and proceed
   directly to creation from scratch.
2. **Creation step.** Participants compose or edit a melody and submit it to
   the market.

After submission, the participant's new melody should enter the rolling
inventory. When the inventory exceeds its fixed capacity, the oldest item
should drop out. The experiment should continue for the same number of
participant rounds as in the reference implementation.

### Adoption interface

When previewing market items, participants should be able to listen to each
melody before choosing one. The preview should focus on playback rather than
showing the underlying note pattern. A waveform visualization is optional, but
the note grid itself should not be shown in the market view.

Where the reference experiment supports a popularity-information condition,
participants in that condition should still see the same adoption statistics as
in the original (for example how often each item was proposed to and selected by
other participants). Participants in the no-popularity condition should see the
market without those statistics.

### Creation interface

The melody editor should be a step sequencer similar to the provided reference
sketch:

- Three pitch rows labelled **Do**, **Re**, and **Mi**.
- Nine time slots.
- Overlapping notes are allowed: more than one pitch row may be active in the
  same time slot.
- Distinct colours for each pitch row.
- A **Play melody** button that audibly previews the current sequence.

Participants should be able to toggle notes on and off by clicking cells. The
experiment should synthesize or otherwise generate the corresponding audio for
preview and for market playback.

The creation step should support the same two regimes as the reference
experiment:

- **From scratch** when the participant has no adopted starting melody, or when
  the market is not yet large enough for adoption.
- **Edit an adopted melody** when the participant selected a market item on the
  previous page.

Apply analogous edit limits to the reference implementation: stricter limits
when editing an adopted melody, and more generous limits when composing from
scratch. Validation should reject empty melodies and responses that exceed the
allowed number of note changes.

### Instructions and debrief

Rewrite the instruction pages, recruitment text, and post-task survey so they
describe melodies rather than drawings. Any screenshots of the original game
that appear in the instructions should also be replaced or adapted so they show
the melody market and step-sequencer interface rather than the drawing task.
Preserve the original two-condition design and the overall structure of the
debrief questions, adapting wording to music creation and adoption strategies.

## Implementation requirements

- Use PsyNet imitation chains and rolling-inventory node logic equivalent to the
  reference `GridNode` / `GridCreateTrial` design.
- Preserve the reference experiment's chain counts, trials per participant,
  inventory pool size, adoption enablement rules, ancestry tracking, and
  popularity accounting unless a music-specific constraint makes a literal copy
  impossible. If a parameter must change, document the reason in the attempt
  README.
- Record enough metadata to reconstruct each submitted melody, the selected
  adoption target, inventory updates, popularity counts, audio pre-screening
  outcome, and condition assignment.
- Do not implement or require the original experiment's mouse movement tracking,
  stroke event tracking, or drawing-specific interaction logs.
- Include bot tests that can complete adoption and creation rounds locally.
- Run successfully with `psynet test local` using only local PsyNet defaults.
  Do not require real Prolific credentials, AWS secrets, or other production
  services.

## Evidence

Submitted evidence should demonstrate:

- Participants encounter an audio pre-screening step before the main market task.
- A participant can preview market melodies with audio playback.
- A participant can compose or edit a melody in the step-sequencer interface
  and hear it with **Play melody**.
- Adoption and creation rounds advance correctly, including the first empty-market
  round and later rolling-inventory updates.
- Both popularity-information and no-popularity conditions render appropriately.
- Automated bots can complete the experiment end to end.
