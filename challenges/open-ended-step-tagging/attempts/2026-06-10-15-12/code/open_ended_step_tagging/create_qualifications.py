"""Generate Cint/Lucid qualification files for this experiment.

Real deployment files are written as:
    qualifications/lucid/lucid-<LANGUAGE>-<COUNTRY>.json

The current ENG-US output is mock-only so the experiment can import locally
before real deployment targets and qualification filters are chosen.
"""

import json
from pathlib import Path

from tqdm import tqdm


# Enable only deployment targets that the experimenter explicitly requested.
# Verify each pair with ``psynet lucid locale`` before uncommenting it.
country_language_tags = (
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


# Mock-only targets keep local imports/tests working while real targets are
# undecided. Mock files are not deployable.
use_mock_only_targets = True
mock_only_country_language_tags = (
    ("ENG", "US"),
)
mock_only_country_language_ids = {
    ("ENG", "US"): 9,
}


# Enable only qualifications explicitly requested by the experimenter.
question_answer_dict = {
    # "IS_NATIVE V1": ["Yes"],
    # "MONOLINGUALISM v1": ["I was raised with my native language only"],
    # "BORN_IN_COUNTRY v1": ["Yes"],
    # "LIVE_IN_COUNTRY v1": ["Yes"],
    # "HAS_NATIONALITY v1": ["Yes"],
    # "HAS_AUDIO v1": ["Yes"],
}


def write_mock_only_config(language_tag, country_tag, config_path):
    country_language_id = mock_only_country_language_ids.get((language_tag, country_tag))
    if country_language_id is None:
        raise SystemExit(
            f"No mock CountryLanguageID for {language_tag}-{country_tag}. "
            "Do not guess; add an explicitly verified mock ID or choose a "
            "different mock-only target."
        )

    config_path.write_text(
        json.dumps(
            {
                "mock_only": True,
                "survey": {
                    "CountryLanguageID": country_language_id,
                    "FulcrumExchangeAllocation": 0,
                    "FulcrumExchangeHedgeAccess": True,
                    "IndustryID": 30,
                    "StudyTypeID": 1,
                    "UniqueIPAddress": True,
                    "UniquePID": True,
                    "BidIncidence": 66,
                    "CollectsPII": False,
                },
                "qualifications": [],
                "country": country_tag,
                "language": language_tag,
            },
            indent=4,
        )
        + "\n",
        encoding="utf-8",
    )


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
            "target tuples commented out and use mock-only files for local "
            "import checks."
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


def generate_mock_only_configs(output_dir):
    for language_tag, country_tag in tqdm(mock_only_country_language_tags):
        config_path = output_dir / f"mock-lucid-{language_tag}-{country_tag}.json"
        write_mock_only_config(language_tag, country_tag, config_path)


output_dir = Path("qualifications/lucid")
output_dir.mkdir(parents=True, exist_ok=True)

if country_language_tags:
    generate_real_configs(output_dir)
elif use_mock_only_targets and mock_only_country_language_tags:
    generate_mock_only_configs(output_dir)
else:
    raise SystemExit(
        "No Cint/Lucid targets enabled. Uncomment real country_language_tags "
        "after the experimenter chooses deployment targets, or enable a "
        "mock-only target for local import checks."
    )
