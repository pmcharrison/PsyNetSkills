# Preregistered qualitative expectations

## Target experiment

The target study is a compact PsyNet word-pair memory experiment. Participants
study cue-target word pairs, then choose the remembered target from four options.
Trials include literal pairs and interference pairs where one option is a recent
target from another pair. The task is suitable for simulation because profile
differences should appear in condition-level accuracy and in the type of lure
selected when memory fails.

## Planned simulated participant profiles

- `psynet_bot_rule`: a PsyNet bot-style profile that follows the trial's correct-answer rule and should behave like an attentive participant.
- `scripted_noisy`: a scripted profile that sometimes guesses and should show lower accuracy with weak condition specificity.
- `mock_llm_memory_limited`: a deterministic prompt-style profile that reads a prompt representation, remembers gist more than order, and should be vulnerable to recent-target lures.
- `semantic_bias`: a scripted profile that overuses semantically related lures, especially on interference trials.

## Expected response patterns

- `psynet_bot_rule` should be near ceiling in both literal and interference conditions.
- `scripted_noisy` should be clearly above random only when the target is visually salient and should have the slowest simulated response times.
- `mock_llm_memory_limited` should do reasonably well on literal trials but often choose the recent lure on interference trials.
- `semantic_bias` should produce a distinctive semantic-lure error pattern and lower interference accuracy.

## Expected failure modes

- The initial instructions may not warn participants strongly enough that recent words can be lures.
- The export may omit enough profile metadata to connect anomalies to simulator behavior.
- A prompt-style simulator may overfit the target label if the prompt accidentally reveals the correct answer too directly.

## Revision trigger

Revise the workflow if the initial analysis shows either (a) interference trials
produce profile-specific lure errors consistent with unclear instructions, or
(b) exported rows cannot be traced cleanly back to profile, condition, and run
metadata. The preferred revision is to clarify the memory instruction and add
explicit profile/run metadata to the export rather than changing the core task.
