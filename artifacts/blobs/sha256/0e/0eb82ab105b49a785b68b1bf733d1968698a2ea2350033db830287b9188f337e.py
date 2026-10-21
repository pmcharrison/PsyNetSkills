"""Generate Cint/Lucid qualification files for this experiment.

Real deployment files are written as:
    qualifications/lucid/lucid-<LANGUAGE>-<COUNTRY>.json

This script is ready to generate the requested qualification files once valid
Lucid API access is configured in the local/deployment environment.
"""

from pathlib import Path

from tqdm import tqdm


# Enable only deployment targets that the experimenter explicitly requested.
# Verify each pair with ``psynet lucid locale`` before uncommenting it.
country_language_tags = (
    ("ENG", "GB"),
    # ("TUR", "TR"),
    # ("GER", "DE"),
    # ("FRE", "FR"),
    # ("JPN", "JP"),
    # ("ENG", "GB"),
    # ("ENG", "US"),
    # ("DUT", "NL"),
    # ("SPA", "ES"),
    # ("ITA", "IT"),
    # ("FIN", "FI"),
    # ("CHI", "SG"),
    # ("CHI", "CN"),
    # ("KOR", "KR"),
    # ("ARA", "EG"),
    # ("POR", "BR"),
)


# Enable only qualifications explicitly requested by the experimenter.
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
            "Configure them in the local/deployment environment, or leave real "
            "target tuples commented out until the experimenter can generate "
            "qualification files locally."
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
        "TIMEOUT": service_qualifications["TIMEOUT v1"],
        # "LIVE_IN_COUNTRY v1": 223200,
        # "HAS_AUDIO v1": 223188,
        # "BORN_IN_COUNTRY v1": 223178,
        # "HAS_NATIONALITY v1": 223205,
        # "IS_NATIVE V1": 223187,
        # "MONOLINGUALISM v1": 223176,
        # "TIMEOUT v1": 223198,
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

if country_language_tags:
    generate_real_configs(output_dir)
else:
    raise SystemExit(
        "No Cint/Lucid targets enabled. Uncomment real country_language_tags "
        "after the experimenter chooses deployment targets."
    )
