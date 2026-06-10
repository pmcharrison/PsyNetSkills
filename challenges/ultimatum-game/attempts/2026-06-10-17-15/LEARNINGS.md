# Learnings

## Use `python3` in minimal Cursor Cloud shells

The shell does not expose `python`, so setup scripts that assume it can fail before creating attempt metadata.

*Actions:*
- **PsyNetSkills:** Consider changing attempt setup examples to call `python3` or `uv run python` explicitly. Confidence: medium. Status: considering.

## Browser evidence needs action paths independent from WebSocket readiness

The live UI rendered and grouped participants, but manual testing showed action clicks could be lost when they depended solely on a ready WebSocket. Posting authenticated actions to a normal experiment route while keeping WebSockets for broadcasts made the participant path reliable.

*Actions:*
- **PsyNetSkills:** Consider adding this HTTP-action-plus-WebSocket-broadcast pattern to synchronous challenge guidance. Confidence: medium. Status: considering.

## Vendored ES modules may require sibling build files

The latest Three.js module imports `three.core.min.js`; vendoring only `three.module.min.js` caused browser-only failures that automated bot tests could not catch.

*Actions:*
- **PsyNetSkills:** For challenges requiring vendored browser libraries, document checking browser network logs for secondary module imports. Confidence: high. Status: considering.

## Evidence must cover negative paths named in the instructions

The public instructions explicitly required timeout behavior evidence, but the submitted participant video only demonstrated successful offer/decision rounds and completion.

*Actions:*
- **PsyNetSkills:** Consider adding an evidence checklist reminder to record at least one timeout path when a challenge names timeout behavior as a central requirement. Confidence: high. Status: considering.

## Visual requirements need direct review against the prompt sketch

The evaluator judged that the interface did not satisfy the requested 3D tabletop environment, even though the implementation used Three.js elements. Future attempts should compare the rendered UI against the prompt sketch before finalizing evidence.

*Actions:*
- **PsyNetSkills:** Consider adding a visual-fidelity review step for challenges with explicit interface sketches or 3D scene requirements. Confidence: medium. Status: considering.

## Interaction evidence should match specified controls and framing

After the Three.js interface update, the evaluator still noted that the proposal interaction did not visibly use the slider and that the video only showed a partial view. Future recordings should frame the full browser viewport and demonstrate the exact control named in the instructions when one is specified.

*Actions:*
- **PsyNetSkills:** Consider adding an evidence-framing reminder for UI challenges: capture the full relevant viewport and use the specified controls, not only faster helper controls. Confidence: high. Status: considering.
