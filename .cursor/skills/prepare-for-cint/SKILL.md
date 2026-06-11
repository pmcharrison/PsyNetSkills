---
name: prepare-for-cint
description: Prepare a PsyNet experiment for Cint/Lucid recruitment by adding required recruiter settings, locale and wage parameters, qualification-generation tooling, and readiness validation.
authors: [elif22]
---

# Prepare for Cint

Use this skill when the user asks to make an existing PsyNet experiment ready
for Cint/Lucid recruitment. The deliverable is an applied, committed experiment
change plus a Cint Readiness Report, not a live EC2/SSH deployment.

This skill owns Cint/Lucid recruiter parameters and qualification files. For
translation marking or POT extraction, use `prepare-for-translation`. For server
provisioning, SSH deployment, export, app destruction, or EC2 teardown, use
`psynet-deployment-ops`.

## Required reads

- Read the target experiment's `experiment.py`, `config.txt`,
  `requirements.txt`, existing `qualifications/`, `locales/`, and deployment
  notes before editing.
- Inspect any existing `create_qualifications.py`, `qualifications.py`, or
  Lucid/Cint helper scripts. Preserve existing entries and comments.
- Read `.cursor/skills/prepare-for-cint/references/create_qualifications_template.py`
  before creating a new qualification-generation script.

## Workflow

### Phase 1 - Deployment context

Collect and maintain a small in-memory deployment context:

- experiment short ID;
- deployment targets as language-country pairs, when known;
- PsyNet locale for each target;
- Lucid language and country tags for each target;
- requested Lucid qualifications;
- wage source and per-target `wage_per_hour`;
- generated qualification files.

If targets are unknown, continue with parameter preparation and qualification
tooling, but mark target-specific deployment readiness as incomplete. Do not
invent languages, countries, locales, wages, or real qualification files.

### Phase 2 - Verify Cint prerequisites

1. Verify the experiment can be made Cint-ready without changing its scientific
   logic, timeline, assets, database settings, custom variables, or data schemas.
2. Determine locale codes from PsyNet's supported locales; do not guess. If a
   target locale is missing, stop target-specific readiness and report it.
3. Verify `locales/<locale>/LC_MESSAGES/experiment.po` exists for every known
   target locale. Do not run translation generation in this skill.
4. Determine Lucid language-country tags with `psynet lucid locale`; do not
   guess or approximate tags.
5. Determine wages from the experimenter's approved wage table, commonly
   `minimum_wage_countries.csv`. If no approved wage source is available, leave
   `wage_per_hour` as a documented blocker rather than guessing.

### Phase 3 - Add Cint parameters to `experiment.py`

Make the smallest safe edit.

1. Add the import if missing:
   `from psynet.recruiters import get_lucid_settings`.
2. Add or update module-level target constants:
   `LANGUAGE`, `COUNTRY`, and `LUCID_CONFIG_PATH`.
3. Add or update `recruiter_settings = get_lucid_settings(...)` with explicit
   timeouts, `debug_recruiter`, and `bid_incidence`.
4. Merge Cint keys into the class-level `Exp.config` dictionary. Keep `config`
   inside `class Exp(...)`; do not move it to module scope.
5. Required keys are:
   - `"recruiter": "lucid"`;
   - `"locale": "<target locale>"`;
   - `**recruiter_settings`;
   - `"wage_per_hour": <approved wage>`;
   - `"publish_experiment": True`.
6. Preserve existing config keys such as `supported_locales`, storage settings,
   custom variables, and database settings. If multiple target locales are
   planned, include them in `supported_locales`.

If no real target is known, use clearly marked placeholder values only when the
experiment must import locally, and report that the experiment is Cint-parameter
ready but not target-ready.

### Phase 4 - Create qualification tooling

Prefer a script named `create_qualifications.py`. If the experiment already uses
another script name, preserve that name unless there is a strong reason to
standardize.

1. Create or update the script from the reference template.
2. Enable only requested deployment target tuples in `country_language_tags`.
   Comment out unused tuples instead of deleting them.
3. Enable only qualifications explicitly requested by the experimenter in
   `question_answer_dict`. Never auto-enable filters such as native language,
   nationality, audio, or monolingualism.
4. Preserve existing entries in `qualifications_dict`. If PsyNet raises
   `Unknown question TIMEOUT`, add the alias:
   `"TIMEOUT": service.get_qualifications_dict()["TIMEOUT v1"]`.
5. Write generated files to
   `qualifications/lucid/lucid-<LANGUAGE>-<COUNTRY>.json`.
6. Run the script after targets and qualifications are known.

If no real target has been chosen, provide the script with all real target
tuples commented out. Create a mock qualification file only if it is required
for local import or tests, can be generated without real recruitment secrets or
paid recruitment, and is named and reported as mock-only. A mock file must never
be counted as Cint deployment-ready.

### Phase 5 - Validate readiness

For every known target, verify:

- `LANGUAGE` and `COUNTRY` match the Lucid tags from `psynet lucid locale`;
- `"locale"` matches a PsyNet supported locale;
- `LUCID_CONFIG_PATH` points at the target's generated qualification JSON;
- the qualification JSON exists under `qualifications/lucid/`;
- `wage_per_hour` comes from the approved wage source;
- `locales/<locale>/LC_MESSAGES/experiment.po` exists;
- `python create_qualifications.py` succeeds when real targets are configured;
- the experiment's normal construction or local test command still runs.

## Cint Readiness Report

End with a concise report:

- Cint parameters changed in `experiment.py`;
- target table with locale, Lucid tags, qualification file, and wage status;
- qualifications enabled;
- qualification generation status;
- translation file status;
- mock-only files, if any;
- readiness status: `target-ready`, `parameter-ready only`, or `blocked`.

## Rules

- Preserve existing experiment logic and deployment notes.
- Do not configure, inspect, print, or commit real AWS, Cint, Lucid, Prolific, or
  other production credentials.
- Do not use custom or real service credentials for local readiness work unless
  the user explicitly provides a safe deployment workflow.
- Do not create fake real-looking Lucid files. Mock files must be visibly named
  and documented as not deployable.
- Do not treat missing locales, wages, or qualification decisions as optional;
  report them as blockers for target-specific Cint deployment readiness.
