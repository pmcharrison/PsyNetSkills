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

When real human participants enter, the scheduler should repeatedly compare the
current human count, AI count, total participant count, remaining trial capacity,
and configured AI-human proportion. It should launch only enough bots to restore
the required proportion at that moment, then check again after subsequent human
arrivals or bot completions. Once the configured total participant count or trial
capacity has been reached, recruitment and AI launching should stop.

For future conversions from pure-human experiments to AI or hybrid human-AI
experiments, the required components are:

- configuration parameters for AI proportion, total participant target,
  credential environment variable name, model/base URL, timeout, retry policy,
  and local mock behavior;
- validation for the AI proportion range and other scheduler/API settings;
- a bot-response path that derives the exact same stimulus representation shown
  to humans, builds an AI prompt from it, calls the model API, parses and
  validates output, and returns the original human response format;
- prompt text that mirrors the human-facing instructions without exposing extra
  information;
- shared stimulus construction so human display and AI prompt cannot diverge;
- an active scheduler that meters bot launches against live human arrivals,
  remaining trial capacity, and the target proportion rather than bulk-launching
  the full AI quota;
- tests for pure-human, mixed, and all-AI settings, config validation,
  prompt/stimulus consistency, scheduler behavior, and mocked API calls.

*Actions:*
- **PsyNetSkills:** Add guidance for hybrid-agent challenges to require active scheduler checks of human count, AI count, total participants, remaining trial capacity, and target proportion during live mixed sessions. Confidence: high. Status: considering.
- **PsyNetSkills:** Add a reusable checklist for converting pure-human experiments into AI or hybrid human-AI experiments, covering config, validation, bot response, prompt parity, shared stimuli, active scheduling, and tests. Confidence: high. Status: considering.
- **PsyNet:** Consider documenting recommended patterns for active bot scheduling in mixed human-AI experiments, including trial-capacity checks, repeated proportion checks, recruitment stopping rules, and avoiding bulk AI launches. Confidence: medium. Status: considering.

## Legacy debug exits after completion

`psynet debug local --legacy` shuts down after recruitment and experiment
completion. That behavior can look like a crash to a researcher expecting the
dashboard to remain open after a short local run.

*Actions:*
- **PsyNetSkills:** Add a note to researcher-facing launch workflows that legacy debug mode exits on experiment completion, and recommend non-legacy debug or larger trial/recruitment targets when the dashboard should remain available. Confidence: medium. Status: considering.
