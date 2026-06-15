# Learnings

## Reuse evaluation learning before implementation

The second attempt benefited from reviewing the previous learning note before
writing code: the plan now separates the evaluator task, requires full-browser
recording playback checks, and keeps PsyNet launch-generated files ignored.

*Actions:*
- **PsyNetSkills:** Consider making second-attempt setup explicitly ask agents to review prior `LEARNINGS.md` files before drafting `PLAN.md`, while still avoiding hidden criteria and previous implementation code unless the user requests it. Confidence: medium. Impact: medium. Status: considering.

## Review participant videos before accepting them

The first participant recording saved during this attempt was cropped and only
showed a hung first iteration. Video review caught the problem before it was
treated as final evidence, and a repeatable Playwright recording produced a
clean 1280x720 walkthrough.

*Actions:*
- **PsyNetSkills:** Make video-review verification a required final check for challenge attempts that include participant recordings, especially when the instructions require all compared stimuli to be visible. Confidence: high. Impact: high. Status: considering.

## Align evaluator fixtures with intended chain outputs

The independent evaluator initially rated a fixed generated SVG that was not the
final selected rendition from the local demonstration. Video review identified
the ambiguity, and the evaluator fixture was changed to rate the final AI-led
refinement candidate used in the walkthrough.

*Actions:*
- **PsyNetSkills:** Clarify that independent evaluator demos should document whether evaluator stimuli are sampled from all generated candidates, selected chain outputs, or a fixed review fixture. Confidence: high. Impact: medium. Status: considering.

## Implement independent ratings as independent experiments

Human evaluation clarified that a separate rating task inside the same
participant flow is not sufficient for this challenge; the rating component
should be an independent experiment.

*Actions:*
- **PsyNetSkills:** For challenges that ask for an independent evaluator or rating experiment, require a separate runnable PsyNet experiment or clearly separate entry point, with evidence showing the rater can be launched independently from the main participant chain. Confidence: high. Impact: high. Status: considering.

## Remove blank participant-facing placeholders

Human evaluation flagged blank placeholders on the experiment page as a quality
issue. Placeholder panels used for first-iteration or pre-generation states need
meaningful text, hidden empty regions, or an alternate layout.

*Actions:*
- **PsyNetSkills:** Add a participant-evidence review check that no submitted participant-facing page contains blank placeholder panels, empty comparison slots, or disabled-looking areas without explanatory text. Confidence: high. Impact: medium. Status: considering.

## Verify real subagent role execution

Human evaluation found that the subagent intended to act as the code generator
did not work properly in that role. Evidence for role-based subagents should
prove that the subagent's output is actually used in the relevant workflow, not
only saved as a side artifact or replaced by a local mock.

*Actions:*
- **PsyNetSkills:** When a challenge attempt uses real subagents as experimental roles, require evidence that each subagent's output is consumed by the implemented workflow or explicitly document why a mock replaced that role. Confidence: high. Impact: high. Status: considering.
