---
name: tweak-interface
description: Modify only PsyNet participant interface elements while preserving experiment logic, trial structure, nodes, and networks.
authors: [eandrade-lotero]
---

# Tweak a PsyNet interface

Use this skill when asked to adjust the participant-facing interface of an
existing PsyNet experiment without changing the experiment design.

## Scope boundary

Only modify interface-layer code:

- `Page` classes and page factories;
- `Control` classes and control configuration;
- prompts, labels, instructions, feedback, and validation messages;
- PsyNet event-management hooks that affect display or interaction timing.

Do not modify experiment logic:

- trials or trial subclasses;
- trial makers;
- nodes or node makers;
- networks, chains, source selection, or propagation behavior.

If the requested interface change appears to require changing trials,
trial makers, nodes, or networks, stop and report the boundary conflict instead
of making a hidden design change.

## Required reads

1. Read `psynet-experiment-implementation/SKILL.md` for the general PsyNet setup
   and validation expectations.
2. Read the target experiment's interface code and the code that instantiates
   those pages or controls.
3. If collecting visual evidence for a challenge attempt, read
   `record-participant-video/SKILL.md`.
4. If the interface text is multilingual, cross-cultural, or intended for later
   localization, read `prepare-for-translation/SKILL.md` before editing text.

## Workflow

1. Identify the exact interface elements to change and list the files that own
   them.
2. Confirm the implementation can stay within pages, controls, prompts, or
   events. Keep trials, trial makers, nodes, and networks read-only.
3. Make the smallest interface-layer edit that satisfies the request. Prefer
   PsyNet-native pages, controls, prompts, events, and `dominate.tags` page
   structure over custom browser code.
4. Create a separate minimal preview experiment that shows the changed interface
   in a simple `Timeline`. This preview should exercise the relevant pages,
   controls, prompts, or events without copying or modifying the experiment's
   trial maker, nodes, or network.
5. Run the preview experiment and capture a simple screenshot for static changes
   or a short video for dynamic behavior.
6. Run the target experiment's existing tests or the narrowest `psynet test local`
   check that proves the interface still loads.
7. Audit the final diff before committing: no behavior changes should appear
   outside the allowed interface-layer files unless the user explicitly approved
   a scope expansion.

## Validation checklist

- The participant can see and interact with the changed interface.
- The separate preview timeline demonstrates the interface without relying on
  trials, trial makers, nodes, or networks.
- Existing trial allocation, node construction, network growth, scoring, and data
  schema remain unchanged.
- Screenshot or video evidence shows the changed interface clearly.
- Any bot path that reaches the modified page or control still returns the same
  formatted answer shape as the browser path.

## Common failures

- Do not move display-only changes into a `Trial` subclass just because the page
  is normally shown from a trial.
- Do not alter a trial maker or network to make the preview easier to run.
- Do not let a demo preview replace testing the real target experiment path.
- Do not present a screenshot of the wrong experiment as proof that the target
  interface changed.
