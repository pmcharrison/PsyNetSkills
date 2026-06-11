"""Template for generating Cint/Lucid qualification files.

Copy this file to the experiment root as ``create_qualifications.py`` and edit
only the target tuples and requested qualifications for the current deployment.

Real deployment files are written as:
    qualifications/lucid/lucid-<LANGUAGE>-<COUNTRY>.json

Mock-only files, when explicitly enabled for local import checks, are written as:
    qualifications/lucid/mock-lucid-<LANGUAGE>-<COUNTRY>.json

Mock files are not deployable.
"""

from pathlib import Path

from tqdm import tqdm

from psynet.lucid import get_lucid_service
from psynet.lucid.qualifications import create_lucid_recruitment_config
from psynet.utils import get_config


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
    # ("GRE", "GR"),
    # ("BUL", "BG"),
    # ("CZE", "CZ"),
    # ("DAN", "DK"),
    # ("HRV", "HR"),
    # ("EST", "EE"),
    # ("HEB", "IL"),
    # ("HUN", "HU"),
    # ("LIT", "LT"),
    # ("NOR", "NO"),
    # ("POL", "PL"),
    # ("HIN", "IN"),
    # ("IND", "ID"),
    # ("POR", "PT"),
    # ("RUM", "RO"),
    # ("RUS", "RU"),
    # ("SRP", "RS"),
    # ("SLK", "SK"),
    # ("SLV", "SI"),
    # ("SWE", "SE"),
    # ("UKR", "UA"),
    # ("URD", "PK"),
    # ("VIE", "VN"),
    # ("THA", "TH"),
    # ("MAY", "MY"),
    # ("ENG", "AU"),
    # ("ENG", "IN"),
    # ("ENG", "NG"),
    # ("SPA", "AR"),
    # ("SPA", "MX"),
    # ("SPA", "CO"),
    # ("SPA", "DO"),
    # ("SWA", "KE"),
    # ("SWA", "TZ"),
    # ("TGL", "PH"),
    # ("AFR", "ZA"),
    # ("AMH", "ET"),
    # ("ARA", "SA"),
    # ("ARA", "AE"),
    # ("ARA", "QA"),
    # ("ARA", "KW"),
    # ("BEN", "IN"),
    # ("FRE", "CA"),
    # ("FRE", "CH"),
    # ("FRE", "BE"),
    # ("FRE", "CM"),
    # ("LAT", "LV"),
    # ("POR", "BR"),
    # ("ZUL", "ZA"),
)


# Use mock-only targets only when local import/tests need a placeholder and the
# experimenter has not decided real targets yet. Verify these tags before use.
use_mock_only_targets = False
mock_only_country_language_tags = (
    # ("ENG", "US"),
)


# Enable only requested qualifications. Leave examples commented unless the
# experimenter explicitly requests them.
question_answer_dict = {
    # "IS_NATIVE V1": ["Yes"],
    # "MONOLINGUALISM v1": ["I was raised with my native language only"],
    # "BORN_IN_COUNTRY v1": ["Yes"],
    # "LIVE_IN_COUNTRY v1": ["Yes"],
    # "HAS_NATIONALITY v1": ["Yes"],
    # "HAS_AUDIO v1": ["Yes"],
}


def target_iterator():
    if country_language_tags:
        return country_language_tags, "lucid-{language_tag}-{country_tag}.json"

    if use_mock_only_targets and mock_only_country_language_tags:
        return (
            mock_only_country_language_tags,
            "mock-lucid-{language_tag}-{country_tag}.json",
        )

    raise SystemExit(
        "No Cint/Lucid targets enabled. Uncomment real country_language_tags "
        "after the experimenter chooses deployment targets, or enable a "
        "mock-only target for local import checks."
    )


config = get_config()
service = get_lucid_service(config=config)
service_qualifications = service.get_qualifications_dict()

qualifications_dict = {
    **service_qualifications,
    # Some PsyNet/Lucid versions expect the unversioned TIMEOUT alias.
    "TIMEOUT": service_qualifications["TIMEOUT v1"],
    # "LIVE_IN_COUNTRY v1": 223200,
    # "HAS_AUDIO v1": 223188,
    # "BORN_IN_COUNTRY v1": 223178,
    # "HAS_NATIONALITY v1": 223205,
    # "IS_NATIVE V1": 223187,
    # "MONOLINGUALISM v1": 223176,
    # "TIMEOUT v1": 223198,
}


tags, filename_template = target_iterator()
output_dir = Path("qualifications/lucid")
output_dir.mkdir(parents=True, exist_ok=True)

for language_tag, country_tag in tqdm(tags):
    config_path = output_dir / filename_template.format(
        language_tag=language_tag,
        country_tag=country_tag,
    )

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
