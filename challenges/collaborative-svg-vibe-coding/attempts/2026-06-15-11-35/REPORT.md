# Report

## Summary

This attempt implements a local PsyNet demonstration of collaborative SVG vibe
coding. Participants iteratively guide a code generator to recreate a
user-supplied cat reference image as SVG. The implementation includes three
role-allocation states in one chain: human-led, hybrid, and AI-led. It also
implements an independent similarity evaluator task that hides role and prompt
metadata.

## Implementation

The experiment lives in `code/collaborative_svg_vibe_coding/`. It uses a
within-participant PsyNet chain for the collaborative iterations and a separate
static trial maker for evaluator ratings. The reference stimulus is the
Google Drive cat image supplied by the user, downloaded into
`static/references/cat.png` and registered in `static/references/manifest.json`.

The code generator receives only:

1. a system prompt identifying it as the code generator;
2. the high-level instruction.

Reference identifiers, previous SVG state, and iteration numbers remain
experiment-side metadata for storage, analysis, and deterministic local replay.
The deterministic mock generator is credential-free and has a visibly distinct
refinement style for the final AI-led iteration.

SVG output is parsed as XML and restricted to a conservative inline SVG subset.
Rejected or malformed SVGs are stored with render-error metadata rather than
silently advanced.

## Evidence

- `evidence/code_generator_subagent.md` records the real code-generator subagent
  invocation using only the system prompt and high-level instruction.
- `evidence/participant.mp4` shows the full-browser participant walkthrough:
  human instruction, SVG generation, human selection, AI-led generation and
  selection, independent evaluator rating, and completion.
- `evidence/simulated_data.zip` contains the `psynet simulate` export.
- `evidence/analyses/analysis.ipynb` reads the simulated export and summarizes
  chain trials, prompt isolation, selector choices, and evaluator ratings.
- `evidence/logs/psynet_test_and_simulate_final.txt` records the final PsyNet
  test and simulation command output.

## Validation

Final automated checks passed:

- `python -m py_compile experiment.py`
- `psynet test local`
- `psynet simulate`
- `npm run participant-flow`
- `jupyter nbconvert --to notebook --execute --inplace evidence/analyses/analysis.ipynb`

The participant video was reviewed with the video-review subagent after a first
recording was rejected for cropping and missing later task pages. The final
review confirmed the 1280x720 viewport is uncropped and shows all required task
stages.

## Limitations

The local generator is a deterministic mock, not a real model provider. Real
provider mode is intentionally optional and would require credentials supplied
through the environment. The attempt is not yet marked complete in `agent.json`
because the human GitHub author key has not been provided.
