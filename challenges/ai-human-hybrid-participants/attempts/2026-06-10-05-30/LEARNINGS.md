# Learnings

## Sensitive config registration

PsyNet refuses to launch when a key registered as sensitive is present in `config.txt`, even if the configured value is only the name of an environment variable. Register actual secret values as sensitive, but keep non-secret indirection keys non-sensitive.

*Actions:*
- **PsyNetSkills:** Add a short note to experiment implementation guidance about keeping API-key environment variable names non-sensitive while marking real token-bearing config keys as sensitive. Confidence: medium. Status: considering.

## Copied demos may need `.python-version`

`psynet test local` passed without a copied `.python-version`, but `psynet debug local --legacy` required it during constraints checks. Challenge attempts adapted from demos should include `.python-version` before evidence collection.

*Actions:*
- **PsyNetSkills:** Update the attempt skill's demo-copy checklist to include `.python-version` alongside `.gitignore` and regenerated constraints. Confidence: high. Status: considering.
