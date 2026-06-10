---
title: Single chord emotion replication
type: experiment implementation
difficulty: 9
authors: [pmcharrison]
---

Implement a PsyNet experiment that reimplements the web-based chord-emotion
rating study reported by Lahdelma and Eerola (2016), "Single chords convey
distinct emotional qualities to both naive and expert listeners." The source
paper is provided in `references/`.

The experiment should follow the standards of a real replication study. Treat
the paper as the primary specification: extract the study design, stimuli,
questionnaires, participant procedure, data fields, and analyses from the paper
and its cited sources rather than relying on this challenge prompt to enumerate
them.

The experiment should:

- Implement the full participant-facing experiment described in the paper,
  including background questionnaires, stimulus presentation, rating scales,
  instructions, randomization, replay behavior, and completion flow.
- Reconstruct the audio stimuli as accurately as practical. The original paper
  used commercial Pro Tools/Ivory and Vienna Symphonic Library sounds; use an
  analogous local solution, such as built-in PsyNet/JSSynth synthesis, and
  document the reconstruction.
- Save enough structured data and metadata to audit every presented stimulus,
  participant response, questionnaire response, and reconstruction choice.
- Include analysis scripts or notebooks that replicate the analyses reported in
  the paper as closely as practical from exported PsyNet data.
- Provide a simulated-data workflow so the analysis can be run without live
  participants. It should generate example participant metadata, questionnaire
  values, randomized trial-level ratings, and enough signal to demonstrate the
  expected analysis outputs.
- Generate example stimulus features from the reconstructed stimuli or their
  metadata so the analysis scripts can demonstrate the feature-based checks
  described in the paper.
- Include a detailed `README.md` or methods note for the implemented experiment.
  The README should describe the complete methodological procedure step by
  step, and each step should cite the exact source for the implementation
  decision. Use short quotations from the original paper where appropriate,
  with page, section, figure, table, or appendix references, and cite any
  external sources used to reconstruct questionnaires or stimuli. The README
  should explicitly state every deviation from the original procedure, why it
  was necessary, and how it might affect replication fidelity.

Do not use custom or real service credentials. The experiment should run
locally with PsyNet's standard development setup.
