---
score: 8
---

# Evaluation

## Summary

The human evaluator scored the attempt 8/10. The code quality and use of core
PsyNet functionality were strong, but the initial reviewed attempt missed two
presentation details: the top progress bar remained blue rather than neutral
gray, and the attempt summary did not embed a PNG of the requested analysis
figure.

## Strengths

- Code structure looks strong.
- The implementation uses core PsyNet functionality appropriately.

## Weaknesses

- The top progress bar was still blue, despite the psychophysics guidance to use
  neutral UI chrome.
- The analysis figure requested in the challenge was present in the notebook but
  not embedded as a PNG in the attempt summary.

## Criteria

- [ ] Reaction time should be measured using JavaScript only in a minimal and
  isolated way. Reaction-time measurement should be closely tied to native events
  in PsyNet's event-management system. Where possible, existing reaction-time
  mechanisms in PsyNet Control classes should be used.
- [ ] The highest priority is the correct display of all visual elements with
  the specified timing. No additional or lingering display elements should
  appear, including fixation crosses, previous stimuli, previous probes, or
  unrelated graphical components not specified in the design.
- [ ] Numbered stimuli should be clearly arranged around the fixation cross,
  with item numbers visually associated with the corresponding stimuli.
- [ ] The probe, response question, and response buttons should be centered
  relative to the stimulus display.
- [ ] Participant-facing displays should not include technical labels or
  implementation-related text, such as labeling the array as "stimuli" or the
  probe as "probe" unless this wording is part of the participant instructions.
- [ ] Make sure that PsyNet nodes and trial constructs are used correctly. Nodes
  may represent individual trial configurations, including set size, stimulus
  identities, positions, numbers, and probe identity, or trial configurations may
  be generated within finalize_trial, provided that all relevant metadata is
  recorded.
- [ ] Make sure keyboard mapping occurs only during the response phase, and
  keyboard strokes are mapped correctly to the numbered response options while
  still enabling mouse clicks.
- [ ] Implementation should use native PsyNet elements like
  KeyboardPushButtonControl as much as possible. PsyNet's documentation describes
  experiments as timelines composed of pages/trials, with ModularPage combining
  a participant-facing prompt and a response Control, and with Trial/Node
  constructs used to organize trial definitions and reusable configurations.

## Notes

- Score and feedback should come from a human evaluator, captured
  conversationally when working with Cursor Cloud Agents.
- Implementation and first-pass evidence collection are complete. Criteria
  checkboxes are left for a human evaluator.
- Post-evaluation repairs neutralized the top progress bar and embedded
  `evidence/analyses/empirical_matrices.png` in `REPORT.md`.
