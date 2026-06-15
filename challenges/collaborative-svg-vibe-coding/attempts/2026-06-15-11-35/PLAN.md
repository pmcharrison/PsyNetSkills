# Plan

## Science

This attempt will implement a local PsyNet version of the collaborative SVG vibe-coding paradigm from Hu et al. (2026). The experiment will model how human and AI guidance affect iterative reconstruction of a reference animal image as SVG code. The local demonstration will prioritize the role structure, participant-facing workflow, deterministic mock AI behavior, and clean chain/evaluator data over full-scale recruitment or real model comparisons.

The attempt will explicitly address the first attempt's learning notes: the independent similarity evaluator will be implemented as a separate participant task, not embedded in the collaborative chain flow, and the participant evidence recording will show the full browser viewport with all reference and generated SVG candidates visible.

## Methods

The collaborative-chain task will present participants with a reference animal image and, after the first iteration, the current best generated SVG rendition. On instructor trials, participants will write high-level natural-language guidance for a coding assistant. A deterministic mock code generator will produce SVG code from the reference identifier, iteration number, previous SVG state, and normalized guidance. From the second candidate onward, selector trials will present the reference image, the previous best SVG, and the newly generated SVG side by side; selectors will choose which candidate advances to the next iteration and may optionally give a short rationale.

The local stimulus set will include a cat reference image for the primary browser walkthrough. If the Google Drive cat image supplied by the user can be downloaded without credentials, it will be saved as a local stimulus asset with provenance recorded; otherwise the attempt will use a local generated cat reference and document the Drive link as a replacement source for human testing. The stimulus loader will use a manifest so additional animal references can be added without changing trial logic.

The implementation will support three role-allocation conditions: human-led, AI-led, and hybrid. Role assignment will be stored at the iteration level for instructor and selector roles. Human-facing pages will describe the immediate task without exposing hidden condition labels; condition and role metadata will be saved in exported data for reconstruction and analysis.

The independent evaluator task will be a separate PsyNet entry point or separately configured participant flow. Evaluators will see one reference image and one generated SVG rendition at a time and rate visual similarity on a labeled numeric scale. Evaluator pages will not show prompts, role allocation, model/provider labels, or condition names.

## Implementation

The attempt code will live under `code/collaborative_svg_vibe_coding/` to avoid importing an experiment package named `code`. It will use PsyNet pages/modules for the instruction, instructor, selector, and evaluator workflows, with custom templates or static assets as needed for side-by-side visual comparison. Chain state will be represented by immutable SVG generation records and iteration records that reference `previous_best_svg_id`, `candidate_svg_id`, and `selected_svg_id`.

The mock AI layer will be isolated behind a provider interface with explicit `mock` and optional `real` modes. Mock mode will be deterministic and credential-free. Real provider mode, if sketched, will only read credentials from environment variables and will remain optional. A code-generator subagent has already been used during planning to specify this interface; implementation will preserve that split by keeping SVG generation separate from participant page logic.

SVG handling will be conservative. Generated SVG will be parsed as XML, restricted to a small safe subset of elements and attributes, rejected for scripts, event handlers, `foreignObject`, external references, oversized content, and data URLs, and stored with render status and any error message. Invalid SVG records may be shown as explicit error placeholders but will not silently advance as valid images.

The participant evidence flow will be designed around two real subagent roles requested by the user: a participant-role subagent for participant-facing review and a code-generator subagent for generation behavior. During implementation and evidence collection, the participant-role subagent will be used to exercise or review the browser flow, and the code-generator subagent's design will be reflected in deterministic mock SVG generation. The canonical participant recording will start on the first task page, not on setup/debug pages, and will cover the whole browser viewport.

Generated PsyNet launch artifacts such as `source_code.zip`, `.deploy/`, `dump.rdb`, `Dockertag`, and `static/assets/` will be ignored in the experiment `.gitignore`.

## Validation and evidence plan

Functional validation will run from the experiment directory with `python experiment.py`, `psynet test local`, and `psynet simulate`. The simulation export will be saved as `evidence/simulated_data.zip`. The analysis notebook will be saved as `evidence/analyses/analysis.ipynb`, executed headlessly, and will summarize chain progression, role assignments, selector choices, render status, and evaluator similarity ratings.

Interactive evidence will use a short full-browser recording, saved as `evidence/participant.mp4`, that shows the cat reference image, an instructor submitting natural-language guidance, deterministic SVG generation, a selector comparing previous and current candidates, and a separate evaluator similarity-rating trial. Playback will be checked before completion to confirm the full browser and all SVG candidates are visible.

`REPORT.md` will summarize the implementation, validation results, simulation limitations, and any blocked checks. The attempt will not be marked complete until the simulation export, executed analysis notebook, participant evidence, and report are present, or any missing artifact is explicitly recorded as a blocker in `EVALUATION.md`.

## Human review

Implementation is paused here for the required human planning review. After approval, the next step is to implement `code/collaborative_svg_vibe_coding/` according to this plan, then collect evidence and complete the report.
