# Learnings

## Translation extraction requires gettext in the agent image

`psynet translate hi fr` failed until the system `gettext` package provided
`xgettext`. The repository instructions list this dependency, but this VM still
needed it installed during the attempt.

*Actions:*
- **PsyNetSkills:** Consider adding a lightweight startup check or environment setup reminder that verifies `xgettext --version` before cross-cultural challenge attempts begin. Confidence: high. Impact: medium. Status: considering.

## Dallinger verification package excludes loose data files

The first `psynet test local` run failed because `data/trials.json` was not
available inside Dallinger's temporary verification package. Moving the manifest
into an importable Python module made the static trial definitions available in
both direct script execution and packaged deployment contexts.

*Actions:*
- **PsyNetSkills:** Consider documenting that challenge attempts should either store small deterministic manifests in importable Python modules or explicitly verify package-data inclusion before relying on loose local data files. Confidence: medium. Impact: medium. Status: considering.
