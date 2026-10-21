# Single chord emotion replication

This experiment reimplements the single-chord emotion rating study reported by Lahdelma and Eerola (2016), "Single chords convey distinct emotional qualities to both naive and expert listeners."

## What is implemented

1. A PsyNet experiment with consent, volume calibration, demographic questions, a short mood questionnaire, the Ollen Musical Sophistication Index workflow, and 28 randomized chord-rating trials.
2. Reconstructed audio stimuli for the 14 C-root chord spellings used in the paper, each rendered in piano and string timbres for a total of 28 stimuli.
3. A deterministic simulation workflow that generates participant metadata, PANAS-like mood scores, OMSI scores, and trial-level ratings with the qualitative patterns described in the paper.
4. An analysis script that summarizes family-level emotion ratings, timbre differences, reliability, and feature correlations from simulated data or exported PsyNet trial data.

## Methodological reconstruction notes

- The experiment follows the paper's participant flow: demographic questions first, then a brief mood questionnaire, then musical sophistication, then the main chord-rating phase.
- The chord set matches the paper's description on pages 9-11: major, minor, diminished, and augmented triads plus dominant, minor, and major seventh chords, including the reported inversions.
- Every stimulus lasts exactly 4.0 seconds and uses equal temperament, matching the paper's description on page 10.
- The rating dimensions follow the appendix definitions in the paper: valence, tension, energy, nostalgia/longing, melancholy/sadness, interest/expectancy, happiness/joy, tenderness, and liking/preference.
- Replay is enabled on every trial to match the instruction on page 12 that participants could listen "as many times as they preferred".

## Source citations for implementation decisions

- Demographics: age, gender, nationality, and education are explicitly listed in the procedure section on page 11.
- Mood questionnaire: the procedure section states that a 10-item PANAS with five positive and five negative adjectives was administered before the chord ratings on page 12.
- OMSI: the participants section states that musical sophistication was measured with the 10-item Ollen Musical Sophistication Index on page 8, and the item wording and scoring coefficients are taken from Ollen (2006), Appendix P and Appendix Q.
- Emotion scale definitions: appendix pages 45-46 provide the short explanations used for the nine rating dimensions.
- Stimulus reconstruction: the paper reports Bosendorfer/Ivory piano and Vienna Chamber Strings samples with light reverb on page 10. This replication uses deterministic additive synthesis with timbre-specific harmonic envelopes and light algorithmic reverb because the original commercial sample libraries are not available in the challenge environment.

## Known deviations and their likely effect

- The original commercial piano and string sample libraries are replaced by deterministic additive synthesis. This preserves pitch content, duration, neutral articulation, and the broad piano-versus-strings contrast, but it will not perfectly reproduce the original timbral detail.
- The paper does not list the exact five positive and five negative PANAS adjectives in the article text. This implementation uses a standard 10-item short-form approximation drawn from the full PANAS vocabulary and records that choice in the exported data.
- The original web app reportedly revealed some scale explanations only after user interaction. In PsyNet's native rating control, the dimension explanations are shown directly with each rating scale instead of as hover-only text.
- The OMSI age item is derived from the demographic age page instead of being asked twice.
- The analysis script focuses on descriptive replication targets and feature correlations. It does not currently reproduce the paper's full repeated-measures ANOVA table because the challenge environment does not bundle the same statistical stack that the original authors used.

## Running the experiment

From this directory, using the PsyNet environment:

1. `python synthesize_stimuli.py`
2. `psynet test local`
3. `psynet debug local`

## Running the simulation and analyses

1. `python simulate_data.py --output-dir simulated_data`
2. `python analysis.py --input simulated_data --output-dir analysis_outputs`

The analysis outputs are written as JSON and Markdown so they can be inspected without a notebook environment.
