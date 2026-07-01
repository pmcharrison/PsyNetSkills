from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import textwrap
from pathlib import Path
from typing import Any


DEFAULT_PSYNET_COMMIT = "bd50a55faed0bd3679df9de00997f951e1e3b467"
REQUIRED_KEYS = {
    "rationale",
    "validities",
    "trial_a_ratings",
    "trial_b_ratings",
    "max_trials",
}

TRANSLATIONS = {
    "hi": {
        "Welcome": "स्वागत है",
        "Welcome to this decision-making task.": "इस निर्णय-निर्माण कार्य में आपका स्वागत है।",
        "You will compare two options described by numerical feature ratings.": "आप संख्यात्मक विशेषता रेटिंग से वर्णित दो विकल्पों की तुलना करेंगे।",
        "Instructions": "निर्देश",
        "On each trial, compare Option A and Option B.": "प्रत्येक ट्रायल में विकल्प A और विकल्प B की तुलना करें।",
        "Each row shows a feature, its validity from 0 to 1, and each option's rating.": "प्रत्येक पंक्ति एक विशेषता, 0 से 1 तक उसकी वैधता, और प्रत्येक विकल्प की रेटिंग दिखाती है।",
        "Higher validities indicate features that are more predictive in the design.": "अधिक वैधता वाली विशेषताएं इस डिजाइन में अधिक पूर्वानुमानकारी हैं।",
        "Choose the option you would prefer. There are no right or wrong answers.": "वह विकल्प चुनें जिसे आप पसंद करेंगे। कोई सही या गलत उत्तर नहीं है।",
        "Decision {TRIAL_NUMBER} of {TOTAL_TRIALS}": "{TOTAL_TRIALS} में से निर्णय {TRIAL_NUMBER}",
        "Please compare both options before choosing.": "चुनने से पहले दोनों विकल्पों की तुलना करें।",
        "Rating": "रेटिंग",
        "Rating {RATING_NUMBER}": "रेटिंग {RATING_NUMBER}",
        "Validity": "वैधता",
        "Value": "मान",
        "Option A": "विकल्प A",
        "Option B": "विकल्प B",
        "Choose Option A": "विकल्प A चुनें",
        "Choose Option B": "विकल्प B चुनें",
        "Thank you": "धन्यवाद",
        "Thank you for completing the decision-making task.": "निर्णय-निर्माण कार्य पूरा करने के लिए धन्यवाद।",
    },
    "de": {
        "Welcome": "Willkommen",
        "Welcome to this decision-making task.": "Willkommen zu dieser Entscheidungsaufgabe.",
        "You will compare two options described by numerical feature ratings.": "Sie vergleichen zwei Optionen, die durch numerische Merkmalsbewertungen beschrieben werden.",
        "Instructions": "Anleitung",
        "On each trial, compare Option A and Option B.": "Vergleichen Sie in jedem Durchgang Option A und Option B.",
        "Each row shows a feature, its validity from 0 to 1, and each option's rating.": "Jede Zeile zeigt ein Merkmal, seine Validität von 0 bis 1 und die Bewertung jeder Option.",
        "Higher validities indicate features that are more predictive in the design.": "Höhere Validitäten kennzeichnen Merkmale, die in diesem Design aussagekräftiger sind.",
        "Choose the option you would prefer. There are no right or wrong answers.": "Wählen Sie die Option, die Sie bevorzugen würden. Es gibt keine richtigen oder falschen Antworten.",
        "Decision {TRIAL_NUMBER} of {TOTAL_TRIALS}": "Entscheidung {TRIAL_NUMBER} von {TOTAL_TRIALS}",
        "Please compare both options before choosing.": "Bitte vergleichen Sie beide Optionen, bevor Sie wählen.",
        "Rating": "Bewertung",
        "Rating {RATING_NUMBER}": "Bewertung {RATING_NUMBER}",
        "Validity": "Validität",
        "Value": "Wert",
        "Option A": "Option A",
        "Option B": "Option B",
        "Choose Option A": "Option A wählen",
        "Choose Option B": "Option B wählen",
        "Thank you": "Vielen Dank",
        "Thank you for completing the decision-making task.": "Vielen Dank, dass Sie die Entscheidungsaufgabe abgeschlossen haben.",
    },
}


EXPERIMENT_TEMPLATE = r'''
from pathlib import Path
import json

import pandas as pd
from dominate import tags

import psynet.experiment
from psynet.modular_page import ModularPage, PushButtonControl
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker
from psynet.utils import get_translator


_ = get_translator(namespace="experiment")
ROOT = Path(__file__).parent
TRIALS = json.loads((ROOT / "generated_trials.json").read_text(encoding="utf-8"))
DESIGN_METADATA = json.loads((ROOT / "design_metadata.json").read_text(encoding="utf-8"))
TOTAL_TRIALS = len(TRIALS)


def option_label(option_id):
    if option_id == "option_a":
        return _("Option A")
    if option_id == "option_b":
        return _("Option B")
    raise ValueError(f"Unknown option ID: {option_id}")


def option_choice_label(option_id):
    if option_id == "option_a":
        return _("Choose Option A")
    if option_id == "option_b":
        return _("Choose Option B")
    raise ValueError(f"Unknown option ID: {option_id}")


def rating_label(rating_index):
    return _("Rating {RATING_NUMBER}").format(RATING_NUMBER=rating_index + 1)


def option_card(option_id, ratings, validities):
    card = tags.div(_class="card h-100 shadow-sm")
    with card:
        tags.div(option_label(option_id), _class="card-header fw-bold text-center")
        with tags.div(_class="card-body p-2"):
            with tags.table(_class="table table-sm align-middle mb-0"):
                with tags.thead():
                    with tags.tr():
                        tags.th(_("Rating"), scope="col")
                        tags.th(_("Validity"), scope="col")
                        tags.th(_("Value"), scope="col")
                with tags.tbody():
                    for i, (validity, rating) in enumerate(zip(validities, ratings)):
                        with tags.tr():
                            tags.td(rating_label(i))
                            tags.td(f"{validity:.2f}")
                            tags.td(str(rating))
    return card


class ChoiceTrial(StaticTrial):
    time_estimate = 0.5

    def show_trial(self, experiment, participant):
        definition = self.definition
        left_id = definition["left_option_id"]
        right_id = definition["right_option_id"]
        option_ratings = {
            "option_a": definition["option_a_ratings"],
            "option_b": definition["option_b_ratings"],
        }
        prompt = tags.div()
        with prompt:
            tags.h3(
                _("Decision {TRIAL_NUMBER} of {TOTAL_TRIALS}").format(
                    TRIAL_NUMBER=definition["trial_index"] + 1,
                    TOTAL_TRIALS=TOTAL_TRIALS,
                )
            )
            tags.p(_("Please compare both options before choosing."))
            with tags.div(_class="row g-3"):
                with tags.div(_class="col-md-6"):
                    option_card(left_id, option_ratings[left_id], definition["validities"])
                with tags.div(_class="col-md-6"):
                    option_card(right_id, option_ratings[right_id], definition["validities"])
        return ModularPage(
            "choice",
            prompt,
            control=PushButtonControl(
                choices=[left_id, right_id],
                labels=[option_choice_label(left_id), option_choice_label(right_id)],
                arrange_vertically=False,
                bot_response=left_id,
            ),
            time_estimate=self.time_estimate,
        )

    def score_answer(self, answer, definition):
        return 1.0


nodes = [StaticNode(definition=trial) for trial in TRIALS]

trial_maker = StaticTrialMaker(
    id_="autocog_choices",
    trial_class=ChoiceTrial,
    nodes=nodes,
    expected_trials_per_participant=len(nodes),
    max_trials_per_participant=len(nodes),
    target_n_participants=1,
    recruit_mode="n_participants",
)


class Exp(psynet.experiment.Experiment):
    label = "AutoCog-compatible human decision-making task"
    test_n_bots = 12

    timeline = Timeline(
        InfoPage(
            tags.div(
                tags.h2(_("Welcome")),
                tags.p(_("Welcome to this decision-making task.")),
                tags.p(
                    _(
                        "You will compare two options described by numerical feature ratings."
                    )
                ),
            ),
            time_estimate=0.5,
        ),
        InfoPage(
            tags.div(
                tags.h2(_("Instructions")),
                tags.p(_("On each trial, compare Option A and Option B.")),
                tags.p(
                    _(
                        "Each row shows a feature, its validity from 0 to 1, and each option's rating."
                    )
                ),
                tags.p(
                    _(
                        "Higher validities indicate features that are more predictive in the design."
                    )
                ),
                tags.p(
                    _(
                        "Choose the option you would prefer. There are no right or wrong answers."
                    )
                ),
            ),
            time_estimate=1.0,
        ),
        trial_maker,
        InfoPage(
            tags.div(
                tags.h2(_("Thank you")),
                tags.p(_("Thank you for completing the decision-making task.")),
            ),
            time_estimate=0.5,
        ),
    )

    def test_check_bot(self, bot, **kwargs):
        assert not bot.failed
        trials = bot.all_trials
        assert len(trials) == TOTAL_TRIALS
        assert all(trial.answer in {"option_a", "option_b"} for trial in trials)
        assert all(trial.definition["validities"] == DESIGN_METADATA["validities"] for trial in trials)

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trials = []
        for trial in ChoiceTrial.query.all():
            definition = trial.definition
            trials.append(
                {
                    "id": trial.id,
                    "participant_id": trial.participant_id,
                    "trial_index": definition["trial_index"],
                    "source_pair_index": definition["source_pair_index"],
                    "presentation_swapped": definition["presentation_swapped"],
                    "left_option_id": definition["left_option_id"],
                    "right_option_id": definition["right_option_id"],
                    "validities": json.dumps(definition["validities"]),
                    "option_a_ratings": json.dumps(definition["option_a_ratings"]),
                    "option_b_ratings": json.dumps(definition["option_b_ratings"]),
                    "answer": trial.answer,
                    "complete": trial.complete,
                    "score": trial.score,
                }
            )
        participants = [
            {
                "id": participant.id,
                "status": participant.status,
                "bonus": participant.bonus,
            }
            for participant in Participant.query.all()
        ]
        return {
            "trial": pd.DataFrame.from_records(trials),
            "participant": pd.DataFrame.from_records(participants),
        }


if __name__ == "__main__":
    print(f"Loaded {TOTAL_TRIALS} generated trials.")
    print(f"Feature count: {len(DESIGN_METADATA['validities'])}")
'''


def load_config(path: Path) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location("autocog_input_config", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not import config file: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "config"):
        raise ValueError("Config file must define a Python dictionary named 'config'.")
    config = module.config
    if not isinstance(config, dict):
        raise ValueError("'config' must be a dictionary.")
    return config


def validate_config(config: dict[str, Any]) -> None:
    missing = REQUIRED_KEYS - set(config)
    if missing:
        raise ValueError(f"Missing required config key(s): {', '.join(sorted(missing))}")
    validities = config["validities"]
    if not isinstance(validities, list) or not validities:
        raise ValueError("'validities' must be a non-empty list.")
    if not all(isinstance(value, (int, float)) for value in validities):
        raise ValueError("All validities must be numeric.")
    if not all(0 <= float(value) <= 1 for value in validities):
        raise ValueError("All validities must be between 0 and 1 inclusive.")
    a_ratings = config["trial_a_ratings"]
    b_ratings = config["trial_b_ratings"]
    if not isinstance(a_ratings, list) or not isinstance(b_ratings, list):
        raise ValueError("'trial_a_ratings' and 'trial_b_ratings' must be lists.")
    if not a_ratings:
        raise ValueError("At least one rating pair is required.")
    if len(a_ratings) != len(b_ratings):
        raise ValueError("'trial_a_ratings' and 'trial_b_ratings' must have equal lengths.")
    feature_count = len(validities)
    for side_name, side_ratings in [
        ("trial_a_ratings", a_ratings),
        ("trial_b_ratings", b_ratings),
    ]:
        for index, ratings in enumerate(side_ratings):
            if not isinstance(ratings, list):
                raise ValueError(f"{side_name}[{index}] must be a list.")
            if len(ratings) != feature_count:
                raise ValueError(
                    f"{side_name}[{index}] length {len(ratings)} does not match "
                    f"the {feature_count} configured validities."
                )
            if not all(isinstance(value, (int, float)) for value in ratings):
                raise ValueError(f"{side_name}[{index}] contains a non-numeric rating.")
    max_trials = config["max_trials"]
    if not isinstance(max_trials, int) or max_trials <= 0:
        raise ValueError("'max_trials' must be a positive integer.")
    if max_trials < len(a_ratings):
        raise ValueError(
            "'max_trials' must be at least the number of configured rating pairs "
            "because generated trial lists use complete integer repetitions."
        )


def expand_trials(config: dict[str, Any]) -> list[dict[str, Any]]:
    validate_config(config)
    pair_count = len(config["trial_a_ratings"])
    max_trials = config["max_trials"]
    n_trials = (max_trials // pair_count) * pair_count
    trials = []
    for trial_index in range(n_trials):
        pair_index = trial_index % pair_count
        presentation_swapped = trial_index % 2 == 1
        left_id = "option_b" if presentation_swapped else "option_a"
        right_id = "option_a" if presentation_swapped else "option_b"
        trials.append(
            {
                "trial_index": trial_index,
                "source_pair_index": pair_index,
                "presentation_swapped": presentation_swapped,
                "left_option_id": left_id,
                "right_option_id": right_id,
                "validities": [float(value) for value in config["validities"]],
                "option_a_ratings": config["trial_a_ratings"][pair_index],
                "option_b_ratings": config["trial_b_ratings"][pair_index],
            }
        )
    return trials


def po_quote(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


def po_file(locale: str) -> str:
    lines = [
        'msgid ""',
        'msgstr ""',
        f'"Language: {locale}\\n"',
        '"MIME-Version: 1.0\\n"',
        '"Content-Type: text/plain; charset=UTF-8\\n"',
        '"Content-Transfer-Encoding: 8bit\\n"',
        "",
    ]
    for msgid, msgstr in TRANSLATIONS[locale].items():
        lines.append("#: experiment.py")
        if "{" in msgid:
            lines.append("#, python-brace-format")
        lines.extend([f"msgid {po_quote(msgid)}", f"msgstr {po_quote(msgstr)}", ""])
    return "\n".join(lines)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")


def generate(config_path: Path, output_dir: Path, psynet_commit: str) -> None:
    config = load_config(config_path)
    trials = expand_trials(config)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    metadata = {
        "rationale": config["rationale"],
        "validities": [float(value) for value in config["validities"]],
        "source_pair_count": len(config["trial_a_ratings"]),
        "max_trials": config["max_trials"],
        "generated_trial_count": len(trials),
    }
    write_text(output_dir / "experiment.py", EXPERIMENT_TEMPLATE)
    write_text(output_dir / "__init__.py", "")
    (output_dir / "generated_trials.json").write_text(
        json.dumps(trials, indent=2), encoding="utf-8"
    )
    (output_dir / "design_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    write_text(
        output_dir / "config.txt",
        """
        [Config]
        title = AutoCog-compatible human decision-making task
        description = Compare two options described by numerical feature ratings.
        contact_email_on_error = nobody@example.com
        organization_name = PsyNetSkills
        recruiter = generic
        currency = $
        wage_per_hour = 12.0
        locale = en
        supported_locales = ["en", "hi", "de"]
        """
    )
    write_text(
        output_dir / "requirements.txt",
        f"psynet @ git+https://gitlab.com/PsyNetDev/PsyNet@{psynet_commit}#egg=psynet\n",
    )
    write_text(
        output_dir / ".gitignore",
        """
        __pycache__/
        .pytest_cache/
        .dallinger/
        .deploy/
        local_config.txt
        data/
        Dockertag
        source_code.zip
        node_modules/
        test-results/
        playwright-report/
        static/
        *.mo
        *.pyc
        """
    )
    write_text(
        output_dir / "README.md",
        f"""
        # Generated AutoCog-compatible decision task

        This experiment was generated from `{config_path.name}`.

        - Source rating pairs: {len(config["trial_a_ratings"])}
        - Generated trials: {len(trials)}
        - Features per option: {len(config["validities"])}
        - Supported locales: English (`en`), Hindi (`hi`), German (`de`)
        """
    )
    write_text(
        output_dir / "test.py",
        """
        import os

        import pytest

        pytest_plugins = ["pytest_dallinger", "pytest_psynet"]
        experiment_dir = os.path.dirname(__file__)


        @pytest.mark.parametrize("experiment_directory", [experiment_dir], indirect=True)
        def test_experiment(launched_experiment):
            launched_experiment.test_experiment()
        """
    )
    for locale in ["hi", "de"]:
        write_text(output_dir / f"locales/{locale}/LC_MESSAGES/experiment.po", po_file(locale))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config_path", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--psynet-commit", default=DEFAULT_PSYNET_COMMIT)
    args = parser.parse_args()
    generate(args.config_path, args.output_dir, args.psynet_commit)
    print(f"Generated experiment at {args.output_dir}")


if __name__ == "__main__":
    main()

