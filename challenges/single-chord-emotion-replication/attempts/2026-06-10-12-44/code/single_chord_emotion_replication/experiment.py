from __future__ import annotations

import json
from pathlib import Path

import psynet.experiment
from psynet.asset import asset
from psynet.bot import Bot
from psynet.consent import MainConsent
from psynet.modular_page import (
    AudioPrompt,
    DropdownControl,
    MultiRatingControl,
    ModularPage,
    NumberControl,
    PushButtonControl,
    RadioButtonControl,
    TextControl,
)
from psynet.page import InfoPage, VolumeCalibration
from psynet.timeline import CodeBlock, Event, Timeline, conditional, join
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker
from psynet.utils import FailedValidation, get_country_dict, get_locale

from .questionnaires import (
    OMSI_COMPOSITION_CATEGORIES,
    OMSI_COMPOSITION_LABELS,
    OMSI_CONCERT_CATEGORIES,
    OMSI_CONCERT_LABELS,
    OMSI_COURSEWORK_CATEGORIES,
    OMSI_COURSEWORK_LABELS,
    OMSI_PRACTICE_CATEGORIES,
    OMSI_PRACTICE_LABELS,
    OMSI_TITLE_CATEGORIES,
    OMSI_TITLE_LABELS,
    emotion_scales,
    panas_scales,
    score_omsi,
)
from .synthesize_stimuli import main as synthesize_stimuli

STIMULUS_MANIFEST = Path(__file__).resolve().parent / "generated_stimuli" / "stimulus_manifest.json"


def load_manifest() -> list[dict]:
    if not STIMULUS_MANIFEST.exists():
        synthesize_stimuli()
    return json.loads(STIMULUS_MANIFEST.read_text(encoding="ascii"))


def build_nodes() -> list[StaticNode]:
    return [
        StaticNode(
            definition={
                "stimulus_id": stimulus["stimulus_id"],
                "family": stimulus["family"],
                "symbol": stimulus["symbol"],
                "label": stimulus["label"],
                "inversion": stimulus["inversion"],
                "timbre": stimulus["timbre"],
                "duration_seconds": stimulus["duration_seconds"],
                "sample_rate": stimulus["sample_rate"],
                "midi_notes": stimulus["midi_notes"],
                **{f"feature_{key}": value for key, value in stimulus["features"].items()},
            },
            assets={"stimulus_audio": asset(stimulus["audio_path"])},
        )
        for stimulus in load_manifest()
    ]


class IntegerPage(ModularPage):
    def __init__(self, label: str, prompt: str, minimum: int, maximum: int, bot_response: int):
        self.minimum = minimum
        self.maximum = maximum
        super().__init__(
            label,
            prompt,
            control=NumberControl(bot_response=bot_response),
            time_estimate=5,
            save_answer=label,
        )

    def validate(self, response, **kwargs):
        try:
            answer = int(response.answer)
        except ValueError:
            return FailedValidation("Please provide a whole number.")
        if not (self.minimum <= answer <= self.maximum):
            return FailedValidation(
                f"Please provide a number between {self.minimum} and {self.maximum}."
            )
        return None


class NationalityPage(ModularPage):
    def __init__(self):
        locale = get_locale()
        country_dict = get_country_dict(locale)
        super().__init__(
            "nationality",
            "What is your nationality?",
            control=DropdownControl(
                choices=list(country_dict.keys()) + ["OTHER"],
                labels=list(country_dict.values()) + ["Other / not listed"],
                default_text="Select a nationality",
                bot_response="FI",
            ),
            time_estimate=5,
            save_answer="nationality",
        )


class EducationPage(ModularPage):
    def __init__(self):
        super().__init__(
            "education",
            "What is your highest completed level of education?",
            control=RadioButtonControl(
                [
                    "secondary_or_less",
                    "some_college",
                    "bachelor",
                    "master",
                    "doctorate_or_professional",
                    "prefer_not_to_say",
                ],
                [
                    "Secondary school or less",
                    "Some college or vocational training",
                    "Bachelor's degree",
                    "Master's degree",
                    "Doctorate or professional degree",
                    "Prefer not to say",
                ],
                bot_response="bachelor",
            ),
            time_estimate=5,
            save_answer="education",
        )


class ChoicePage(ModularPage):
    def __init__(self, label: str, prompt: str, choices: list[str], labels: list[str], bot_response: str):
        super().__init__(
            label,
            prompt,
            control=RadioButtonControl(choices, labels, bot_response=bot_response),
            time_estimate=5,
            save_answer=label,
        )


class YesNoPage(ModularPage):
    def __init__(self, label: str, prompt: str, bot_response: str = "yes"):
        super().__init__(
            label,
            prompt,
            control=PushButtonControl(["yes", "no"], ["Yes", "No"], bot_response=bot_response),
            time_estimate=5,
            save_answer=label,
        )


def store_omsi_coursework(participant):
    if participant.var.get("omsi_has_college_music") == "yes":
        choice = participant.var.get("omsi_college_coursework_detail")
    else:
        choice = "none"
    participant.var.set("omsi_college_coursework", choice)


def store_omsi_summary(participant):
    answers = {
        "omsi_age": participant.var.get("age"),
        "omsi_age_started": participant.var.get("omsi_age_started"),
        "omsi_private_lessons_years": participant.var.get("omsi_private_lessons_years"),
        "omsi_regular_practice_years": participant.var.get("omsi_regular_practice_years"),
        "omsi_current_practice_amount": participant.var.get("omsi_current_practice_amount"),
        "omsi_college_coursework": participant.var.get("omsi_college_coursework"),
        "omsi_composition_experience": participant.var.get("omsi_composition_experience"),
        "omsi_concert_attendance": participant.var.get("omsi_concert_attendance"),
        "omsi_self_title": participant.var.get("omsi_self_title"),
    }
    participant.var.set("omsi", score_omsi(answers))


def questionnaire_timeline():
    return join(
        InfoPage(
            "You will first complete a short set of background questions before beginning the chord ratings.",
            time_estimate=5,
        ),
        ChoicePage(
            "gender",
            "How do you identify yourself?",
            ["female", "male", "non_binary", "prefer_not_to_say"],
            ["Female", "Male", "Non-binary", "Prefer not to say"],
            bot_response="female",
        ),
        IntegerPage("age", "What is your age in years?", 17, 90, bot_response=30),
        NationalityPage(),
        EducationPage(),
        InfoPage(
            "Next comes the brief mood questionnaire described in the paper. Please rate how you feel right now.",
            time_estimate=5,
        ),
        ModularPage(
            "panas",
            "Rate each feeling from 1 (very slightly or not at all) to 5 (extremely).",
            control=MultiRatingControl(*panas_scales()),
            time_estimate=30,
            save_answer="panas",
        ),
        InfoPage(
            "The original study measured musical sophistication with the Ollen Musical Sophistication Index (OMSI).",
            time_estimate=5,
        ),
        IntegerPage(
            "omsi_age_started",
            "At what age did you begin sustained musical activity? If never, enter 0.",
            0,
            90,
            bot_response=10,
        ),
        IntegerPage(
            "omsi_private_lessons_years",
            "How many years of private music lessons have you received? If none, enter 0.",
            0,
            80,
            bot_response=5,
        ),
        IntegerPage(
            "omsi_regular_practice_years",
            "For how many years have you engaged in regular daily musical practice or singing? If none, enter 0.",
            0,
            80,
            bot_response=4,
        ),
        ChoicePage(
            "omsi_current_practice_amount",
            "Which category best describes the amount of time you currently spend practicing an instrument or voice?",
            OMSI_PRACTICE_CATEGORIES,
            OMSI_PRACTICE_LABELS,
            bot_response="one_hour_per_week",
        ),
        YesNoPage(
            "omsi_has_college_music",
            "Have you ever enrolled in any music courses offered at college or university?",
            bot_response="no",
        ),
        conditional(
            "omsi_college_music_detail",
            lambda experiment, participant: participant.answer == "yes",
            ChoicePage(
                "omsi_college_coursework_detail",
                "How much college-level coursework in music have you completed?",
                OMSI_COURSEWORK_CATEGORIES[1:],
                OMSI_COURSEWORK_LABELS[1:],
                bot_response="one_or_two_nonmajor_courses",
            ),
        ),
        CodeBlock(store_omsi_coursework),
        ChoicePage(
            "omsi_composition_experience",
            "Which option best describes your experience composing music?",
            OMSI_COMPOSITION_CATEGORIES,
            OMSI_COMPOSITION_LABELS,
            bot_response="never",
        ),
        ChoicePage(
            "omsi_concert_attendance",
            "How many live concerts of any style have you attended as an audience member in the past 12 months?",
            OMSI_CONCERT_CATEGORIES,
            OMSI_CONCERT_LABELS,
            bot_response="one_to_four",
        ),
        ChoicePage(
            "omsi_self_title",
            "Which title best describes you?",
            OMSI_TITLE_CATEGORIES,
            OMSI_TITLE_LABELS,
            bot_response="music_loving_nonmusician",
        ),
        CodeBlock(store_omsi_summary),
    )


class ChordTrial(StaticTrial):
    time_estimate = 18

    def show_trial(self, experiment, participant):
        return ModularPage(
            "single_chord_rating",
            AudioPrompt(
                self.assets["stimulus_audio"],
                text=(
                    "Listen to this single chord as many times as you like. "
                    "Rate the emotional qualities the chord seems to convey."
                ),
                controls={"Play": "Play again"},
            ),
            control=MultiRatingControl(*emotion_scales()),
            events={"submitEnable": Event(is_triggered_by="promptEnd")},
            time_estimate=self.time_estimate,
        )


class Exp(psynet.experiment.Experiment):
    label = "Single chord emotion replication"

    timeline = Timeline(
        MainConsent(),
        VolumeCalibration(),
        InfoPage(
            "This experiment reproduces the web-based single-chord emotion study by Lahdelma and Eerola (2016). Please use headphones and complete the task in one sitting.",
            time_estimate=5,
        ),
        InfoPage(
            "You will hear isolated C-based triads and seventh chords played with piano and string timbres. The order is randomized for each participant.",
            time_estimate=5,
        ),
        questionnaire_timeline(),
        InfoPage(
            "The rating phase begins next. Each chord lasts four seconds and can be replayed as many times as you like before you submit your ratings.",
            time_estimate=5,
        ),
        StaticTrialMaker(
            id_="single_chord_ratings",
            trial_class=ChordTrial,
            nodes=build_nodes,
            expected_trials_per_participant="n_nodes",
            max_trials_per_participant="n_nodes",
        ),
        InfoPage(
            "Thank you for taking part. Your responses have been saved.",
            time_estimate=5,
        ),
    )

    @property
    def ad_requirements(self):
        return super().ad_requirements + [
            'You must wear <strong>headphones</strong> and use a recent Chrome browser.'
        ]

    def test_check_bot(self, bot: Bot, **kwargs):
        assert len(bot.alive_trials) == len(load_manifest())
