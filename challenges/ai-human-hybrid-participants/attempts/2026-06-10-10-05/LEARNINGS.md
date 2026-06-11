# Learnings

## Custom PsyNet config keys need registration

Adding new keys only to `config.txt` or `config_defaults()` is not enough in the
current PsyNet/Dallinger stack; the experiment must also register the keys in
`extra_parameters()` before strict config loading accepts them.

*Actions:*
- **PsyNetSkills:** Add a short note to the hybrid-conversion skill about registering custom Dallinger config keys with `extra_parameters()`. Confidence: high. Impact: low. Status: considering. Notes: This prevented the first full `psynet test local` run from importing the experiment.
## Visual-only participant recordings for silent experiments

The Cursor VM did not expose `pactl`, but this Gibbs task has no experiment
audio. The participant evidence was therefore captured as visual-only X11 video,
with the missing audio stream explicitly documented.

*Actions:*
- **PsyNetSkills:** Consider documenting when visual-only evidence is acceptable for silent experiments. Confidence: medium. Impact: low. Status: considering. Notes: The existing recording skill focuses on audio-capable workflows.
## Hybrid schedulers need AI concurrency caps

The active scheduler tracks the target AI-human proportion, but the evaluation
identified a missing overload safeguard: the scheduler should enforce a
customizable hard cap on concurrently running AI participants, with a hard
default such as 40, and should consider both successful and currently running
bots when deciding whether to launch more AI participants.

*Actions:*
- **PsyNetSkills:** Update the hybrid-conversion skill to require a configurable parallel-AI cap and checks for successful and currently running bots in active schedulers. Confidence: high. Impact: high. Status: considering. Notes: Human evaluation flagged this as the main technical weakness.
## Mixed-proportion human testing should be standardized

The attempt included code-level proportion tests and a live mock AI bot run, but
the evaluation noted that it lacked a standard human-facing procedure for testing
the experiment under multiple AI proportions.

*Actions:*
- **PsyNetSkills:** Add a repeatable evidence procedure for testing human participant flows under pure-human, mixed, and all-AI settings. Confidence: high. Impact: high. Status: considering. Notes: This would make future hybrid attempts easier to evaluate consistently.
## Human instruction pages should feed AI system prompts

The current challenge did not have a separate instruction module beyond the trial
prompt, but future hybrid conversions should treat participant-facing
instruction pages as source material for AI system prompts.

*Actions:*
- **PsyNetSkills:** Extend prompt-parity guidance to require integrating human instruction pages into AI system prompts when such pages exist. Confidence: medium. Impact: high. Status: considering. Notes: Human evaluation identified this as a future improvement.
