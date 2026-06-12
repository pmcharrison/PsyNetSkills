"""Generate Cint/Lucid qualification files for configured deployment targets.

Real deployment files are written as:
    qualifications/lucid/lucid-<LANGUAGE>-<COUNTRY>.json
"""

from pathlib import Path

from tqdm import tqdm


# Requested targets. Run this script only after valid Lucid API credentials are
# configured in the local/deployment environment.
country_language_tags = (
    ("TUR", "TR"),
    ("ARA", "MA"),
    ("ENG", "US"),
    ("FRE", "FR"),
    ("FRE", "CA"),
)


# No optional qualifications were selected. PsyNet's Lucid helper adds TIMEOUT
# automatically.
question_answer_dict = {
    # "IS_NATIVE V1": ["Yes"],
    # "MONOLINGUALISM v1": ["I was raised with my native language only"],
    # "BORN_IN_COUNTRY v1": ["Yes"],
    # "LIVE_IN_COUNTRY v1": ["Yes"],
    # "HAS_NATIONALITY v1": ["Yes"],
    # "HAS_AUDIO v1": ["Yes"],
    # "ALLOW_VOICE_RECORDING v1": ["Yes"],
}


def require_lucid_api_access(config):
    missing = []
    for key in ("lucid_api_key", "lucid_sha1_hashing_key"):
        try:
            config.get(key)
        except KeyError:
            missing.append(key)

    if missing:
        raise SystemExit(
            "Real Cint/Lucid qualification generation requires configured "
            f"{', '.join(missing)}. Do not add real credentials to the repo. "
            "Configure them in the local/deployment environment, then rerun "
            "python create_qualifications.py."
        )


def generate_real_configs(output_dir):
    from psynet.lucid import get_lucid_service
    from psynet.lucid.qualifications import create_lucid_recruitment_config
    from psynet.utils import get_config

    config = get_config()
    require_lucid_api_access(config)
    service = get_lucid_service(config=config)
    service_qualifications = service.get_qualifications_dict()

    qualifications_dict = {
        **service_qualifications,
        # Some PsyNet/Lucid versions expect the unversioned TIMEOUT alias.
        "TIMEOUT": service_qualifications["TIMEOUT v1"],
    }

    for language_tag, country_tag in tqdm(country_language_tags):
        config_path = output_dir / f"lucid-{language_tag}-{country_tag}.json"

        create_lucid_recruitment_config(
            language_tag=language_tag,
            country_tag=country_tag,
            question_answer_dict=question_answer_dict,
            config_path=str(config_path),
            debug=True,
            config=config,
            service=service,
            qualifications_dict=qualifications_dict,
        )


output_dir = Path("qualifications/lucid")
output_dir.mkdir(parents=True, exist_ok=True)
generate_real_configs(output_dir)
