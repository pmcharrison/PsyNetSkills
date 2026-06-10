---
title: Spanish translation of the static demo
type: experiment implementation
difficulty: 4
authors: [jacobyn]
---

Create a translatable Spanish variant of PsyNet's static demo, starting from
`~/PsyNet/demos/experiments/static`.

Use the `prepare-for-translation` skill as the workflow for preparing the demo.
The submitted experiment should be a runnable copy or adaptation of the static
demo in the attempt directory, not a patch to the shared PsyNet checkout. It
should preserve the original task logic while making participant-facing text
available to PsyNet's translation system.

The participant-facing result should run entirely in Spanish when the experiment
locale is Spanish. The experiment should also be easy to switch back to English,
and doing so should leave the original English participant interface unchanged
apart from the translation-enabling code.
