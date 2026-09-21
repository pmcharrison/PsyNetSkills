# Learnings

## Standard PsyNet experiment support files

Creating a PsyNet experiment from scratch rather than copying a demo made it easy to miss the standard `test.py` entrypoint required by `psynet test local`.

*Actions:*
- **PsyNetSkills:** Update `develop-experiment-code` guidance to list the standard PsyNet support files that should be copied or generated for challenge attempts, including `test.py`, `.gitignore`, `config.txt`, `requirements.txt`, and `constraints.txt`. Confidence: high. Impact: medium. Status: considering.

## Custom page JavaScript load order

A custom PsyNet page can render a blank participant page if page-specific JavaScript is loaded before `js_vars` are copied into page globals.

*Actions:*
- **PsyNetSkills:** Add a `develop-experiment-front-end` note that custom templates should load page-specific static scripts after defining globals derived from `psynet.var`, or otherwise read `psynet.var` lazily after page load. Confidence: high. Impact: medium. Status: considering.

## Vendor requested JavaScript before adapting it

When a challenge asks to integrate an existing browser game, preserving the original JavaScript files should be treated as a core requirement unless the instructions explicitly permit a rewrite.

*Actions:*
- **PsyNetSkills:** Update `attempt-challenge` or `develop-experiment-front-end` guidance to require agents to vendor referenced JavaScript source files first, then document any adapter-layer changes separately from the upstream files. Confidence: high. Impact: high. Status: considering.
