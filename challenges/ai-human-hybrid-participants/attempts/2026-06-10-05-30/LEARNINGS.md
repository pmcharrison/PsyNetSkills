# Learnings

## Sensitive config registration

PsyNet refuses to launch when a key registered as sensitive is present in `config.txt`, even if the configured value is only the name of an environment variable. Register actual secret values as sensitive, but keep non-secret indirection keys non-sensitive.

*Actions:*
- **PsyNetSkills:** Add a short note to experiment implementation guidance about keeping API-key environment variable names non-sensitive while marking real token-bearing config keys as sensitive. Confidence: medium. Status: considering.

## Copied demos may need `.python-version`

`psynet test local` passed without a copied `.python-version`, but `psynet debug local --legacy` required it during constraints checks. Challenge attempts adapted from demos should include `.python-version` before evidence collection.

*Actions:*
- **PsyNetSkills:** Update the attempt skill's demo-copy checklist to include `.python-version` alongside `.gitignore` and regenerated constraints. Confidence: high. Status: considering.

## Hybrid scheduling must be active

Launching the full AI quota when the first human enters can let fast bots consume
all Gibbs trials before the human receives any color trials. A hybrid experiment
needs an active scheduler that meters AI launches against human arrivals, trial
capacity, and the desired proportion over time.

*Actions:*
- **PsyNetSkills:** Add guidance for hybrid-agent challenges to test live mixed sessions where humans and AI both receive substantive trials, not only final participant counts. Confidence: high. Status: considering.
- **PsyNet:** Consider documenting recommended patterns for active bot scheduling in mixed human-AI experiments, including trial-capacity checks and avoiding bulk AI launches. Confidence: medium. Status: considering.

## Legacy debug exits after completion

`psynet debug local --legacy` shuts down after recruitment and experiment
completion. That behavior can look like a crash to a researcher expecting the
dashboard to remain open after a short local run.

*Actions:*
- **PsyNetSkills:** Add a note to researcher-facing launch workflows that legacy debug mode exits on experiment completion, and recommend non-legacy debug or larger trial/recruitment targets when the dashboard should remain available. Confidence: medium. Status: considering.
