# Cint Readiness Report

## Experiment parameters

- COMPLETE: Added `get_lucid_settings` import.
- COMPLETE: Added `LANGUAGE = "ENG"`, `COUNTRY = "GB"`, and computed `LUCID_CONFIG_PATH = f"qualifications/lucid/lucid-{LANGUAGE}-{COUNTRY}.json"`.
- COMPLETE: Added class-level `Exp.config` with locale, supported locales, placeholder wage, `publish_experiment`, and Lucid recruiter settings.
- REVIEW: `LANGUAGE`, `COUNTRY`, `locale`, `wage_per_hour`, and the generated qualification file selected by `LUCID_CONFIG_PATH` must be checked before every deployment target.
- REVIEW: Current `experiment.py` placeholder is always ENG-GB for structural import review, not one of the requested deployment targets.

## Parameter review notes

- REVIEW: `termination_time_in_s`, `initial_response_within_s`, `inactivity_timeout_in_s`, `no_focus_timeout_in_s`, and `bid_incidence` are starting values and may need study-specific review.
- REVIEW: `wage_per_hour` is currently a structural placeholder (`12.0`) in `Exp.config`; deployment wages are blank in `cint_deployment_targets.csv` and must be reviewed separately for each country.
- REVIEW: No optional qualification filters were enabled because `MONOLINGUALISM` and `HAS_AUDIO` were provided with unchecked boxes. `TIMEOUT` is added automatically by PsyNet's Lucid helper.

## Deployment targets

| Language | Country | PsyNet locale | Lucid language tag | Lucid country tag | wage_per_hour |
| --- | --- | --- | --- | --- | --- |
| Turkish | Turkey | tr | TUR | TR | |
| Arabic | Morocco | ar | ARA | MA | |
| English | United States | en | ENG | US | |
| French | France | fr | FRE | FR | |
| French | Canada | fr | FRE | CA | |

- COMPLETE: PsyNet locale codes `tr`, `ar`, `en`, and `fr` are supported by the local PsyNet checkout.
- BLOCKED: `psynet lucid locale` could not verify Lucid language-country pair availability because local Lucid API credentials are missing.

## Deployment CSV

- COMPLETE: Created `cint_deployment_targets.csv` with one row for each requested language-country pair.
- REVIEW: `wage_per_hour` is blank for every row and must be filled from an approved wage source before deployment.

## Qualification tooling

- COMPLETE: Created `create_qualifications.py`.
- COMPLETE: Enabled target tuples: `("TUR", "TR")`, `("ARA", "MA")`, `("ENG", "US")`, `("FRE", "FR")`, and `("FRE", "CA")`.
- COMPLETE: No optional filters enabled; examples remain commented for future edits.
- BLOCKED: Real qualification generation requires valid Lucid API access in the local/deployment environment.

## Lucid API access

- MISSING: `psynet lucid locale` failed because `lucid_api_key` is not configured.
- MISSING: `create_qualifications.py` requires `lucid_api_key` and `lucid_sha1_hashing_key` in the local/deployment environment.
- No secret values were inspected, printed, copied, or committed.

## Qualification files

- COMPLETE: Added temporary placeholder `qualifications/lucid/lucid-ENG-GB.json` from the repository's example JSON shape so the experiment imports structurally.
- BLOCKED: Real JSON files for `lucid-TUR-TR.json`, `lucid-ARA-MA.json`, `lucid-ENG-US.json`, `lucid-FRE-FR.json`, and `lucid-FRE-CA.json` must be generated with `python create_qualifications.py` after Lucid API access is configured.
- REVIEW: The ENG-GB placeholder JSON is not a real generated qualification file and must be regenerated before real deployment.

## Translation files

- COMPLETE: Source template `locales/experiment.pot` exists.
- COMPLETE: English source locale can run structurally.
- BLOCKED: `locales/tr/LC_MESSAGES/experiment.po` is missing.
- BLOCKED: `locales/ar/LC_MESSAGES/experiment.po` is missing.
- BLOCKED: `locales/fr/LC_MESSAGES/experiment.po` is missing.

## Validation run

- PENDING: `python experiment.py`.
- PENDING: `psynet translate`.
- PENDING: `psynet test local`.
- PENDING: `python create_qualifications.py`.
- PENDING: `uv run psynetsk-validate`.

## What the experimenter needs to know

- `locale` controls the participant-facing language and must match an existing `.po` file for non-English targets.
- `LANGUAGE` and `COUNTRY` are Lucid market tags; the computed `LUCID_CONFIG_PATH` uses them to select `lucid-<LANGUAGE>-<COUNTRY>.json`.
- `wage_per_hour` is country-specific and should be filled separately for every row in `cint_deployment_targets.csv`.
- `create_qualifications.py` is ready, but real qualification JSON generation requires valid Lucid API credentials in the local/deployment environment.
- `TIMEOUT` is added automatically. Optional filters such as `MONOLINGUALISM` and `HAS_AUDIO` should be enabled intentionally because each one can reduce the qualifying participant pool.
- `termination_time_in_s`, `inactivity_timeout_in_s`, `no_focus_timeout_in_s`, and `bid_incidence` are study-specific review parameters, not universal defaults.

## Remaining decisions/blockers

- Fill or review `wage_per_hour` for every target row.
- Configure Lucid API access locally, then verify target pair availability with `psynet lucid locale`.
- Generate real qualification JSON files with `python create_qualifications.py`.
- Add or review `.po` translation files for Turkish, Arabic, and French targets before deployment.

## Local generation reminder

- After configuring Lucid API keys locally, run: `python create_qualifications.py`.
- This command creates the real qualification JSON files; this readiness pass only prepares the script and placeholder structure because Lucid API access is unavailable.

## Readiness status

- `parameter-ready only`
