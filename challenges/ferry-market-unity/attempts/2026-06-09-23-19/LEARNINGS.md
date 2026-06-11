# Learnings

## Unity WebGL build must be present in PsyNet's packaged static tree

PsyNet's local debug packaging excluded `static/scripts/` when that directory was
listed in `.gitignore`, causing Unity asset 404s even though the files existed
locally. The experiment now extracts the committed WebGL zip into
`static/scripts/` and leaves that directory unignored so PsyNet includes it in
its runtime source package.

*Actions:*
- **PsyNetSkills:** Document that Unity WebGL build assets must be committed or otherwise present in PsyNet's packaged static tree, not hidden by `.gitignore`, for future challenge attempts. Confidence: high. Status: considering.

## Ferry `speed` values are travel delays

The original Ferry Market experiment uses `ferry_speeds` as a wire-field name,
but the values are actually travel delays. A smaller value is faster; the fast
training ferry uses delay `2`.

*Actions:*
- **PsyNetSkills:** Keep the delay semantics note in the challenge instructions and attempt code comments. Confidence: high. Status: completed.
