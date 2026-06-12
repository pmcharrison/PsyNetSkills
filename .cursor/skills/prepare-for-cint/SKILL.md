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

Collect and maintain a small in-memory deployment context. Ask the user for any
missing required values before editing target-specific qualification settings:

- experiment short ID;
- deployment targets as language-country pairs;
- PsyNet locale for each target;
- Lucid language and country tags for each target;
- requested Lucid qualifications;
- per-target `wage_per_hour` review value, which may remain blank until the
  experimenter fills it from an approved wage source;
- generated qualification files.

Ask explicitly:

1. Which language-country pairs do you want to prepare for Cint?
2. Which Lucid qualifications do you want enabled in the study?
3. Which target should be used as the current placeholder in `experiment.py`?

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

### Phase 3 - Add Cint parameters to `experiment.py`

Make the smallest safe edit.

1. Add the import if missing:
   `from psynet.recruiters import get_lucid_settings`.
2. Add or update module-level target constants:
   `LANGUAGE`, `COUNTRY`, and `LUCID_CONFIG_PATH`. Use the user's chosen
   placeholder target if available; otherwise use a clearly marked mock-only
   local placeholder.
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

If no real target is known, use clearly marked placeholder values only when the
experiment must import locally, and report that the experiment is Cint-parameter
ready but not target-ready.

For local tests without Lucid credentials, prefer an explicit environment-gated
mock path over committed credential placeholders. For example,
`PSYNET_CINT_LOCAL_MOCK=1` may switch only the local test recruiter to
`generic`, while the default code path remains Lucid/Cint-ready for deployment.
Report the required environment flag and make clear that real deployments should
leave the mock flag unset.

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
   script only for mock-only local files unless safe Lucid API access is already
   configured.

If no real target has been chosen, provide the script with all real target
tuples commented out. Create a mock qualification file only if it is required
for local import or tests, can be generated without real recruitment secrets or
paid recruitment, and is named and reported as mock-only. A mock file must never
be counted as Cint deployment-ready. Mock files prove local import/test
readiness, not real Cint recruitment readiness.

Always create or preserve one mock-only JSON when `experiment.py` needs a Lucid
config path for local import/tests before real qualification files exist. The
mock file should let the experiment run structurally, but the report must remind
the user to generate real qualifications themselves with valid Lucid API keys.

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

End with a concise report that explicitly lists every required step and whether
it is complete, blocked, skipped, or not applicable. Do not collapse blockers
into a single final status; reviewers should see exactly what remains.

Use this structure:

- `Experiment parameters`: imports, `LANGUAGE`, `COUNTRY`,
  `LUCID_CONFIG_PATH`, `get_lucid_settings`, class-level `Exp.config`, recruiter,
  locale, wage, and `publish_experiment`.
- `Deployment targets`: language-country pairs, PsyNet locale, Lucid tags, and
  source used to verify them. Include an empty `wage_per_hour` column when wages
  have not been supplied.
- `Qualification tooling`: script path, enabled target tuples, enabled filters,
  and whether real generation was attempted.
- `Lucid API access`: available, missing, unusable, or not checked. Never include
  secret values.
- `Qualification files`: real files generated and mock-only files created, with
  mock files clearly marked not deployable.
- `Translation files`: per-target `.po` status.
- `Validation run`: commands run and whether they passed.
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

Deployment targets
| Language | Country | PsyNet locale | Lucid language tag | Lucid country tag | wage_per_hour |
| Turkish  | Turkey  | tr            | TUR                | TR                |               |
| French   | France  | fr            | FRE                | FR                |               |

Qualification tooling
- COMPLETE: Created create_qualifications.py.
- COMPLETE: Enabled country_language_tags = (("TUR", "TR"), ("FRE", "FR")).
- COMPLETE: Enabled requested filters: IS_NATIVE V1, HAS_AUDIO v1.
- BLOCKED: Real qualification JSON generation requires local Lucid API access.

Qualification files
- COMPLETE: Created mock-only qualifications/lucid/mock-lucid-ENG-US.json for
  local import/tests.
- BLOCKED: Real lucid-TUR-TR.json and lucid-FRE-FR.json must be generated by the
  experimenter in their local repo terminal after Lucid credentials are
  configured.

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
- Do not create fake real-looking Lucid files. Mock files must be visibly named
  and documented as not deployable.
- Do not treat missing locales, wages, or qualification decisions as optional;
  report them as blockers for target-specific Cint deployment readiness.
