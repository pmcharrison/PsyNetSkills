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
- Read `.cursor/skills/prepare-for-cint/assets/example_lucid_ENG_GB.json` as a
  shape example for generated Lucid qualification JSON. Do not treat it as a
  deployable qualification file for the target experiment.

## Workflow

### Phase 1 - Deployment context

Collect and maintain a small in-memory deployment context. Ask the user for any
missing required values before editing target-specific qualification settings:

- experiment short ID;
- deployment targets as language-country pairs;
- PsyNet locale for each target;
- Lucid language and country tags for each target;
- requested Lucid qualifications;
- per-target `wage_per_hour` review value, which may remain blank until the
  experimenter fills it from an approved wage source;
- generated qualification files;
- deployment CSV path, usually `cint_deployment_targets.csv`.

Ask explicitly:

1. Which language-country pairs do you want to prepare for Cint?
2. Which Lucid qualifications do you want enabled in the study?
3. Which target should be used as the current placeholder in `experiment.py`?

When asking about qualifications, briefly explain the available custom filters:

- `TIMEOUT`: warning participants that leaving the page or switching context can
  terminate participation; this is set automatically by PsyNet's Lucid helper.
- `MONOLINGUALISM`: asks whether participants were raised with only their native
  language.
- `HAS_AUDIO`: asks whether participants can play audio.
- `ALLOW_VOICE_RECORDING`: asks whether participants can record their voice.
- `BORN_IN_COUNTRY`: asks whether participants were born in the target country.
- `LIVE_IN_COUNTRY`: asks whether participants currently live in the target
  country.
- `HAS_NATIONALITY`: asks whether participants hold the target country's
  nationality.
- `IS_NATIVE`: asks whether participants are native speakers of the target
  language.

If targets are unknown, continue with generic parameter preparation and
qualification tooling, but leave real `country_language_tags` commented out and
mark target-specific deployment readiness as incomplete. Do not invent
languages, countries, locales, wages, or real qualification files.

### Phase 2 - Verify Cint prerequisites

1. Verify the experiment can be made Cint-ready without changing its scientific
   logic, timeline, assets, database settings, custom variables, or data schemas.
2. Determine locale codes from PsyNet's supported locales; do not guess. If a
   target locale is missing, stop target-specific readiness and report it.
3. Verify `locales/<locale>/LC_MESSAGES/experiment.po` exists for every known
   target locale. Do not run translation generation in this skill.
4. Determine Lucid language-country tags with `psynet lucid locale`; do not
   guess or approximate tags.
5. Leave per-target wage values blank in the report unless the user provides an
   approved wage source, commonly `minimum_wage_countries.csv`. Never guess wage
   values. The report should teach the experimenter that `wage_per_hour` must be
   reviewed and set separately for each deployment target.
6. Create or update `cint_deployment_targets.csv` in the experiment root. Include
   one row per requested target and leave `wage_per_hour` blank unless an
   approved wage value was provided. If no targets are known yet, create the file
   with the header only and report that target rows remain blocked.

Required CSV columns:

```text
locale,language,country,language_tag,country_tag,wage_per_hour,qualification_file
```

Use `.cursor/skills/prepare-for-cint/assets/cint_deployment_targets_template.csv`
as the starting point when creating this file.

### Phase 3 - Add Cint parameters to `experiment.py`

Make the smallest safe edit.

1. Add the import if missing:
   `from psynet.recruiters import get_lucid_settings`.
2. Add or update module-level target constants:
   `LANGUAGE`, `COUNTRY`, and `LUCID_CONFIG_PATH`. Use the user's chosen
   placeholder target if available. The default `LUCID_CONFIG_PATH` should point
   to the real deployable path
   `qualifications/lucid/lucid-<LANGUAGE>-<COUNTRY>.json`, not a mock file.
   If the real API-generated file is not available yet, copy the provided Lucid
   JSON shape example to that same path as a temporary placeholder and clearly
   report that the experimenter must regenerate it locally with valid Lucid API
   access before deployment.
3. Add or update `recruiter_settings = get_lucid_settings(...)` with explicit
   timeouts, `debug_recruiter`, and `bid_incidence`.
4. Merge Cint keys into the class-level `Exp.config` dictionary. Keep `config`
   inside `class Exp(...)`; do not move it to module scope.
5. Required keys are:
   - `"recruiter": "lucid"`;
   - `"locale": "<target locale>"`;
   - `**recruiter_settings`;
   - `"wage_per_hour": <approved or placeholder wage>`;
   - `"publish_experiment": True`.
6. Preserve existing config keys such as `supported_locales`, storage settings,
   custom variables, and database settings. If multiple target locales are
   planned, include them in `supported_locales`.

If no real target is known, use clearly marked placeholder `LANGUAGE` and
`COUNTRY` values only when the experiment must import locally, and report that
the experiment is Cint-parameter ready but not target-ready. Keep the real-path
default visible so the experimenter knows what must be generated for deployment.

Teach the experimenter that these `get_lucid_settings` parameters are
study-specific review points:

- `lucid_recruitment_config_path`: must point to the active target's generated
  `qualifications/lucid/lucid-<LANGUAGE>-<COUNTRY>.json`.
- `termination_time_in_s`: maximum time a participant may spend in the
  experiment.
- `debug_recruiter`: use `True` only for local testing; use `False` for real
  Cint/Lucid deployment.
- `initial_response_within_s`: terminates participants who do not reach the first
  response quickly enough.
- `inactivity_timeout_in_s`: terminates after no clicking, typing, scrolling, or
  mouse movement for the configured duration.
- `no_focus_timeout_in_s`: terminates after moving outside the window or opening
  another tab for the configured duration.
- `bid_incidence`: expected percentage of respondents who qualify after basic
  demographic targeting; update it for the study's expected screen-in rate.

### Phase 4 - Create qualification tooling

Prefer a script named `create_qualifications.py`. If the experiment already uses
another script name, preserve that name unless there is a strong reason to
standardize.

1. Create or update the script from the reference template in the experiment
   repo root.
2. Populate `country_language_tags` with the user's requested, verified Lucid
   language-country tuples. Leave unused example tuples commented.
3. Enable the exact qualifications explicitly requested by the experimenter in
   `question_answer_dict`. Leave all other filter examples commented. Never
   auto-enable filters such as native language, nationality, audio, or
   monolingualism.
4. Before claiming real qualification generation, verify that the local PsyNet
   environment can access Lucid through configured `lucid_api_key` and
   `lucid_sha1_hashing_key` values. Do not inspect, print, copy, or commit the
   values. If keys are missing or unusable, stop real generation, leave the
   script ready to run, and mark qualification generation as blocked by missing
   Lucid API access.
5. Preserve existing entries in `qualifications_dict`. If PsyNet raises
   `Unknown question TIMEOUT`, add the alias:
   `"TIMEOUT": service.get_qualifications_dict()["TIMEOUT v1"]`.
6. Write real generated files to
   `qualifications/lucid/lucid-<LANGUAGE>-<COUNTRY>.json`.
7. Tell the user to run the script in their local repo terminal after targets,
   qualifications, and Lucid API access are available. The agent may run the
   script only when safe Lucid API access is already configured.

If no real target has been chosen, provide the script with all real target
tuples commented out and report that target-specific qualification generation is
blocked. When the experiment needs a JSON file to import structurally before
API-backed qualification generation is possible, copy the ENG-GB example JSON
shape to the current `LUCID_CONFIG_PATH` filename. Do not add alternate mock
parameters or `mock-lucid-*` paths in `experiment.py`; instead, remind the user
that this placeholder file must be regenerated in their local repo terminal with
valid Lucid API keys before deployment.

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

### Phase 6 - Explain Cint deployment review points

Every run must include a short, plain-language explanation for experimenters who
are new to Cint/Lucid deployment. Keep it concise, but do not assume they already
know why these values matter:

- `locale`: controls PsyNet's participant-facing language. It must match an
  existing translation file such as `locales/tr/LC_MESSAGES/experiment.po`.
- `LANGUAGE` and `COUNTRY`: Lucid/Cint tags for the recruitment market. They
  must match the active deployment target and the generated JSON filename.
- `wage_per_hour`: the hourly payment rate. Review it separately for every
  country; do not reuse one country's wage for all deployment targets.
- `qualification_file`: the JSON file Cint/Lucid uses for demographic and custom
  qualification targeting. A copied placeholder can support structural review,
  but real deployment needs JSON regenerated with `python create_qualifications.py`
  after valid Lucid API access is configured.
- `create_qualifications.py`: the local script the experimenter runs to create
  real `qualifications/lucid/lucid-<LANGUAGE>-<COUNTRY>.json` files.
- `debug_recruiter`: use `False` for real Cint/Lucid deployment.
- `bid_incidence`: expected percentage of respondents who qualify after the
  chosen targeting and filters. Review it for each study; stricter filters
  usually lower the qualifying pool.
- Timeouts (`termination_time_in_s`, `initial_response_within_s`,
  `inactivity_timeout_in_s`, `no_focus_timeout_in_s`): study-specific limits for
  total participation time, slow starts, inactivity, and leaving the experiment
  window.

## Cint Readiness Report

End with a concise report that explicitly lists every required step and whether
it is complete, blocked, skipped, or not applicable. Do not collapse blockers
into a single final status; reviewers should see exactly what remains.

Use this structure:

- `Experiment parameters`: imports, `LANGUAGE`, `COUNTRY`,
  `LUCID_CONFIG_PATH`, `get_lucid_settings`, class-level `Exp.config`, recruiter,
  locale, wage, and `publish_experiment`.
- `Parameter review notes`: explain which Cint parameters likely need
  experimenter review, especially timeouts, `bid_incidence`, locale, language
  tag, country tag, and per-target wage.
- `Deployment targets`: language-country pairs, PsyNet locale, Lucid tags, and
  source used to verify them. Include an empty `wage_per_hour` column when wages
  have not been supplied.
- `Deployment CSV`: path, rows added, and any blank wage values requiring human
  review.
- `Qualification tooling`: script path, enabled target tuples, enabled filters,
  and whether real generation was attempted.
- `Lucid API access`: available, missing, unusable, or not checked. Never include
  secret values.
- `Qualification files`: real files generated and temporary placeholder JSON
  files created, with placeholders clearly marked as needing regeneration.
- `Translation files`: per-target `.po` status.
- `Validation run`: commands run and whether they passed.
- `What the experimenter needs to know`: concise explanations of locale, Lucid
  tags, wage, qualification files, selected filters, API access, and timing/
  incidence parameters.
- `Remaining decisions/blockers`: targets, filters, locale files, wages, Lucid
  credentials, or anything else needed before deployment.
- `Readiness status`: one of `target-ready`, `parameter-ready only`, or
  `blocked`.

### Example report shape

```text
Cint Readiness Report

Experiment parameters
- COMPLETE: Added get_lucid_settings import.
- COMPLETE: Added LANGUAGE, COUNTRY, and LUCID_CONFIG_PATH.
- COMPLETE: Added class-level Exp.config with recruiter, locale,
  recruiter_settings, wage_per_hour, and publish_experiment.
- REVIEW: LANGUAGE/COUNTRY/locale/wage_per_hour must be updated for each real
  deployment target.
- REVIEW: LUCID_CONFIG_PATH points to lucid-<LANGUAGE>-<COUNTRY>.json; if this
  file was copied from the example JSON, regenerate it before deployment.

Deployment targets
| Language | Country | PsyNet locale | Lucid language tag | Lucid country tag | wage_per_hour |
| Turkish  | Turkey  | tr            | TUR                | TR                |               |
| French   | France  | fr            | FRE                | FR                |               |

Deployment CSV
- COMPLETE: Created cint_deployment_targets.csv with locale, language, country,
  language_tag, country_tag, wage_per_hour, and qualification_file columns.
- REVIEW: wage_per_hour is blank for each target and must be filled before
  deployment.

Qualification tooling
- COMPLETE: Created create_qualifications.py.
- COMPLETE: Enabled country_language_tags = (("TUR", "TR"), ("FRE", "FR")).
- COMPLETE: Enabled requested filters: IS_NATIVE V1, HAS_AUDIO v1.
- BLOCKED: Real qualification JSON generation requires local Lucid API access.

Qualification files
- COMPLETE: Added qualifications/lucid/lucid-ENG-GB.json from the example JSON
  shape so the experiment can import structurally.
- REVIEW: This JSON must be regenerated with create_qualifications.py and valid
  Lucid API access before real deployment.
- BLOCKED: Real lucid-TUR-TR.json and lucid-FRE-FR.json must be generated by the
  experimenter in their local repo terminal after Lucid credentials are
  configured.

Parameter review notes
- REVIEW: termination_time_in_s, initial_response_within_s,
  inactivity_timeout_in_s, no_focus_timeout_in_s, and bid_incidence are
  study-specific.
- REVIEW: locale, LANGUAGE, COUNTRY, LUCID_CONFIG_PATH, wage_per_hour, and the
  generated qualification file must match each deployment target.

What the experimenter needs to know
- locale controls the participant language and must match an existing .po file.
- LANGUAGE and COUNTRY are Lucid market tags; they also determine the
  lucid-<LANGUAGE>-<COUNTRY>.json filename.
- wage_per_hour is country-specific and should be filled separately for every
  row in cint_deployment_targets.csv.
- create_qualifications.py is ready, but real qualification JSON generation
  requires valid Lucid API credentials in the local/deployment environment.
- TIMEOUT is added automatically. Optional filters such as IS_NATIVE,
  BORN_IN_COUNTRY, HAS_AUDIO, and MONOLINGUALISM should be chosen intentionally
  because each one can reduce the qualifying participant pool.
- termination_time_in_s, inactivity_timeout_in_s, no_focus_timeout_in_s, and
  bid_incidence are study-specific review parameters, not universal defaults.

Next local command for the experimenter
- python create_qualifications.py

Readiness status
- parameter-ready only
```

## Rules

- Preserve existing experiment logic and deployment notes.
- Do not configure, inspect, print, or commit real AWS, Cint, Lucid, Prolific, or
  other production credentials.
- Do not use custom or real service credentials for local readiness work unless
  the user explicitly provides a safe deployment workflow.
- Do not claim a copied placeholder Lucid JSON is a real generated
  qualification file. It must be documented as needing regeneration before
  deployment.
- Do not treat missing locales, wages, or qualification decisions as optional;
  report them as blockers for target-specific Cint deployment readiness.
