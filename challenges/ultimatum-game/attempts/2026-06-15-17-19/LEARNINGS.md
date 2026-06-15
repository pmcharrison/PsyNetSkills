# Learnings

## Imported interface templates need explicit contract checks

The requested three.js template came from an attempt with a different
state-update API than the working source experiment. Before treating a visual
template as reusable, compare its `psynet.var` inputs, websocket message names,
and DOM selectors against the source experiment and adapt the interface script
or test runner accordingly.

*Actions:*
- **PsyNetSkills:** Add a short checklist for reusing interface templates across attempts: verify `psynet.var` names, websocket message contracts, static asset paths, and Playwright selectors before collecting screenshots. Confidence: high. Impact: medium. Status: considering.
