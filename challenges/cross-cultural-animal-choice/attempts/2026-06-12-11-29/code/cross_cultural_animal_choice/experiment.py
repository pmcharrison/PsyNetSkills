import random

import pandas as pd
from dominate import tags
from markupsafe import Markup

import psynet.experiment
from psynet.modular_page import KeyboardPushButtonControl, ModularPage
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.recruiters import get_lucid_settings
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker
from psynet.utils import get_locale, get_translator

_ = get_translator(namespace="experiment")

LANGUAGE = "ENG"
COUNTRY = "GB"
LUCID_CONFIG_PATH = f"qualifications/lucid/lucid-{LANGUAGE}-{COUNTRY}.json"

recruiter_settings = get_lucid_settings(
    lucid_recruitment_config_path=LUCID_CONFIG_PATH,
    termination_time_in_s=120 * 60,  # Maximal time a participant can spend.
    debug_recruiter=False,  # Only True during local testing.
    initial_response_within_s=180,  # Terminate if first response is too slow.
    inactivity_timeout_in_s=15 * 60,  # No clicking/typing/scrolling/mouse movement.
    no_focus_timeout_in_s=10 * 60,  # Mouse outside window or another tab.
    bid_incidence=30,  # Percent expected to qualify after targeting.
)

ANIMAL_KEYS = ["cat", "dog", "bird"]
KEYS = ["KeyA", "KeyS", "KeyD"]
KEY_LABELS = ["A", "S", "D"]

PROMPT_TEXT = {
    "companion": "Which animal would you most like to have as a companion?",
    "community_respect": "Which animal do you think is most respected in your community?",
}


def translated_prompt(prompt_key):
    if prompt_key == "companion":
        return _("Which animal would you most like to have as a companion?")
    if prompt_key == "community_respect":
        return _("Which animal do you think is most respected in your community?")
    raise ValueError(f"Unknown prompt key: {prompt_key}")


def translated_animal_label(animal):
    if animal == "cat":
        return _("Cat")
    if animal == "dog":
        return _("Dog")
    if animal == "bird":
        return _("Bird")
    raise ValueError(f"Unknown animal: {animal}")


def animal_button_label(animal, key_label):
    label = translated_animal_label(animal)
    return Markup(
        "<span class='animal-choice-label'>"
        f"<img src='/static/images/{animal}.svg' alt='{label}' class='animal-choice-icon' />"
        f"<span>{label}</span>"
        f"<small><kbd>{key_label}</kbd></small>"
        "</span>"
    )


class AnimalChoiceControl(KeyboardPushButtonControl):
    def __init__(self, *, prompt_key, prompt_text, animal_order):
        self.prompt_key = prompt_key
        self.prompt_text = prompt_text
        self.animal_order = list(animal_order)

        super().__init__(
            choices=self.animal_order,
            keys=KEYS,
            labels=[
                animal_button_label(animal, key_label)
                for animal, key_label in zip(self.animal_order, KEY_LABELS)
            ],
            arrange_vertically=False,
            style="min-width: 150px; margin: 10px; padding: 12px;",
        )

    @property
    def metadata(self):
        return {
            **super().metadata,
            "prompt_key": self.prompt_key,
            "prompt_text": self.prompt_text,
            "animal_order": self.animal_order,
        }

    def format_answer(self, raw_answer, **kwargs):
        participant = kwargs["participant"]
        metadata = kwargs.get("metadata", {})
        selected_animal = str(raw_answer)

        return {
            "prompt_key": self.prompt_key,
            "prompt_text": self.prompt_text,
            "animal_order": self.animal_order,
            "selected_animal": selected_animal,
            "selected_label": translated_animal_label(selected_animal),
            "response_position": self.animal_order.index(selected_animal) + 1,
            "locale": participant.locale or get_locale(),
            "browser_platform": participant.browser_platform or "",
            "reaction_time": metadata.get("time_taken"),
        }


class AnimalChoiceTrial(StaticTrial):
    time_estimate = 8

    def finalize_definition(self, definition, experiment, participant):
        definition = dict(definition)
        animal_order = list(ANIMAL_KEYS)
        random.shuffle(animal_order)
        definition["animal_order"] = animal_order
        return definition

    def show_trial(self, experiment, participant):
        prompt_key = self.definition["prompt_key"]
        prompt_text = PROMPT_TEXT[prompt_key]
        animal_order = self.definition["animal_order"]
        question_number = self.definition["question_number"]

        prompt = tags.div(
            tags.p(
                _("Question {QUESTION_NUMBER} of 2").format(
                    QUESTION_NUMBER=question_number
                ),
                cls="text-muted animal-choice-counter",
            ),
            tags.h2(translated_prompt(prompt_key), cls="animal-choice-question"),
            tags.p(
                _("Click an animal, or press A, S, or D on your keyboard."),
                cls="animal-choice-help",
            ),
        )

        return ModularPage(
            f"animal_choice_{prompt_key}",
            prompt,
            AnimalChoiceControl(
                prompt_key=prompt_key,
                prompt_text=prompt_text,
                animal_order=animal_order,
            ),
            time_estimate=self.time_estimate,
        )


def make_trial_maker(prompt_key, question_number):
    return StaticTrialMaker(
        id_=f"{prompt_key}_choice",
        trial_class=AnimalChoiceTrial,
        nodes=[
            StaticNode(
                definition={
                    "prompt_key": prompt_key,
                    "question_number": question_number,
                }
            )
        ],
        expected_trials_per_participant=1,
        max_trials_per_participant=1,
    )


class Exp(psynet.experiment.Experiment):
    label = "Cross-cultural animal choice"
    test_n_bots = 3

    config = {
        "locale": "en",
        "supported_locales": ["ar", "en", "fr", "tr"],
        "wage_per_hour": 12.0,
        "publish_experiment": True,
        **recruiter_settings,
    }

    timeline = Timeline(
        InfoPage(
            tags.div(
                tags.h1(_("Animal choices")),
                tags.p(
                    _(
                        "In this short experiment, you will answer two questions about familiar animals."
                    )
                ),
            ),
            time_estimate=5,
        ),
        InfoPage(
            tags.div(
                tags.p(
                    _(
                        "On each page, choose one animal from cat, dog, and bird."
                    )
                ),
                tags.p(
                    _(
                        "There are only two questions. Your answers help us compare simple animal preferences across language or locale groups."
                    )
                ),
                tags.p(
                    _(
                        "We record your experiment locale and browser platform, but we do not ask for identifying cultural information."
                    )
                ),
            ),
            time_estimate=8,
        ),
        make_trial_maker("companion", 1),
        make_trial_maker("community_respect", 2),
        InfoPage(
            tags.div(
                tags.h1(_("Thank you")),
                tags.p(_("You have completed the animal choice experiment.")),
            ),
            time_estimate=5,
        ),
    )

    def test_check_bot(self, participant):
        trials = sorted(
            participant.all_trials,
            key=lambda trial: trial.definition["question_number"],
        )
        assert len(trials) == 2
        assert [trial.definition["prompt_key"] for trial in trials] == [
            "companion",
            "community_respect",
        ]
        for trial in trials:
            assert trial.answer["selected_animal"] in ANIMAL_KEYS
            assert trial.answer["selected_animal"] in trial.answer["animal_order"]
            assert trial.answer["response_position"] in [1, 2, 3]
            assert trial.answer["locale"] == "en"

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trials = []
        for trial in StaticTrial.query.all():
            answer = trial.answer or {}
            trials.append(
                {
                    "trial_id": trial.id,
                    "participant_id": trial.participant_id,
                    "prompt_key": trial.definition.get("prompt_key"),
                    "prompt_text": PROMPT_TEXT.get(trial.definition.get("prompt_key")),
                    "question_number": trial.definition.get("question_number"),
                    "animal_order": ",".join(
                        trial.definition.get("animal_order", [])
                    ),
                    "selected_animal": answer.get("selected_animal"),
                    "selected_label": answer.get("selected_label"),
                    "response_position": answer.get("response_position"),
                    "locale": answer.get("locale"),
                    "browser_platform": answer.get("browser_platform"),
                    "reaction_time": trial.time_taken,
                }
            )

        participants = []
        for participant in Participant.query.all():
            participants.append(
                {
                    "participant_id": participant.id,
                    "status": participant.status,
                    "complete": participant.complete,
                    "locale": participant.locale or get_locale(),
                    "browser_platform": participant.browser_platform,
                }
            )

        return {
            "trial": pd.DataFrame.from_records(trials),
            "participant": pd.DataFrame.from_records(participants),
        }


Exp.css_links.append("static/animal-choice.css")


if __name__ == "__main__":
    for index, prompt_key in enumerate(PROMPT_TEXT, start=1):
        print(f"{index}. {PROMPT_TEXT[prompt_key]}")
