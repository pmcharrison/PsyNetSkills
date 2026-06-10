# Learnings

## Custom PsyNet config keys need registration

Adding new keys only to `config.txt` or `config_defaults()` is not enough in the
current PsyNet/Dallinger stack; the experiment must also register the keys in
`extra_parameters()` before strict config loading accepts them.

*Actions:*
- **PsyNetSkills:** Add a short note to the hybrid-conversion skill about registering custom Dallinger config keys with `extra_parameters()`. Confidence: high. Status: considering. Notes: This prevented the first full `psynet test local` run from importing the experiment.

## Visual-only participant recordings for silent experiments

The Cursor VM did not expose `pactl`, but this Gibbs task has no experiment
audio. The participant evidence was therefore captured as visual-only X11 video,
with the missing audio stream explicitly documented.

*Actions:*
- **PsyNetSkills:** Consider documenting when visual-only evidence is acceptable for silent experiments. Confidence: medium. Status: considering. Notes: The existing recording skill focuses on audio-capable workflows.
