import math
import os
import random

from dominate import tags

import psynet.experiment
from psynet.consent import NoConsent
from psynet.modular_page import ModularPage, NumberControl
from psynet.page import InfoPage
from psynet.timeline import CodeBlock, FailedValidation, Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker
from psynet.utils import get_locale, get_translator

_ = get_translator()


CATEGORIES = {
    "life_spans": {
        "unit": "years",
        "t_past_values": [18, 39, 61, 83, 96],
        "base_offset": 58,
        "slope": 0.33,
    },
    "marriages": {
        "unit": "years",
        "t_past_values": [1, 3, 7, 11, 23],
        "base_offset": 17,
        "slope": 0.75,
    },
    "movie_run_times": {
        "unit": "minutes",
        "t_past_values": [30, 60, 80, 95, 110],
        "base_offset": 35,
        "slope": 0.82,
    },
    "poem_lengths": {
        "unit": "lines",
        "t_past_values": [2, 5, 12, 32, 67],
        "base_offset": 5,
        "slope": 1.65,
    },
    "waiting_times": {
        "unit": "minutes",
        "t_past_values": [1, 3, 7, 11, 23],
        "base_offset": 7,
        "slope": 1.75,
    },
}


LOCALE_ADJUSTMENTS = {
    "en": {},
    "it": {
        "marriages": {"offset": 3, "slope": 0.08},
        "waiting_times": {"offset": 1.5, "slope": 0.12},
    },
    "he": {
        "life_spans": {"offset": 2.5, "slope": 0.04},
        "movie_run_times": {"offset": 3, "slope": 0.05},
        "poem_lengths": {"offset": -3, "slope": -0.12},
    },
}


def active_locale():
    return get_locale() or os.environ.get("PSYNET_LOCALE", "en")


def is_rtl_locale(locale):
    return locale in {"he", "ar", "fa", "ur"}


def trial_key(definition):
    return "{CATEGORY}_{T_PAST}".format(
        CATEGORY=definition["category"],
        T_PAST=definition["t_past"],
    )


def unit_label(unit, value):
    if unit == "years":
        return _("year") if value == 1 else _("years")
    if unit == "minutes":
        return _("minute") if value == 1 else _("minutes")
    if unit == "lines":
        return _("line") if value == 1 else _("lines")
    raise ValueError(f"Unknown unit: {unit}")


def category_title(category):
    return {
        "life_spans": _("Life spans"),
        "marriages": _("Lengths of marriages"),
        "movie_run_times": _("Movie run times"),
        "poem_lengths": _("Poem lengths"),
        "waiting_times": _("Waiting times"),
    }[category]


def vignette(definition):
    t_past = definition["t_past"]
    unit = unit_label(definition["unit"], t_past)
    return {
        "life_spans": _(
            "Insurance agencies employ actuaries to make predictions about people's life spans, the age at which they will die. If you were assessing an insurance case for an {T_PAST}-year-old man, what would you predict for his total life span?"
        ).format(T_PAST=t_past),
        "marriages": _(
            "A friend is telling you about an acquaintance whom you do not know. In passing, he happens to mention that this person has been married for {T_PAST} {UNIT}. How long do you think this person's marriage will last in total?"
        ).format(T_PAST=t_past, UNIT=unit),
        "movie_run_times": _(
            "If you made a surprise visit to a friend and found that they had been watching a movie for {T_PAST} {UNIT}, what would you predict for the total length of the movie?"
        ).format(T_PAST=t_past, UNIT=unit),
        "poem_lengths": _(
            "If your friend read you her favorite line of poetry and told you it was line {T_PAST} of a poem, what would you predict for the total length of the poem?"
        ).format(T_PAST=t_past),
        "waiting_times": _(
            "If you were calling a telephone box office to book tickets and had been on hold for {T_PAST} {UNIT}, what would you predict for the total time you would be on hold?"
        ).format(T_PAST=t_past, UNIT=unit),
    }[definition["category"]]


def prediction_for_bot(definition, locale, participant_id):
    params = CATEGORIES[definition["category"]]
    adjustment = LOCALE_ADJUSTMENTS.get(locale, {}).get(definition["category"], {})
    seed = "{LOCALE}:{PARTICIPANT}:{CATEGORY}:{T_PAST}".format(
        LOCALE=locale,
        PARTICIPANT=participant_id,
        CATEGORY=definition["category"],
        T_PAST=definition["t_past"],
    )
    rng = random.Random(seed)
    prediction = (
        params["base_offset"]
        + adjustment.get("offset", 0)
        + (params["slope"] + adjustment.get("slope", 0)) * definition["t_past"]
        + rng.normalvariate(0, max(1.0, definition["t_past"] * 0.04))
    )
    return round(max(definition["t_past"], prediction), 1)


class PredictionControl(NumberControl):
    def __init__(self, definition):
        super().__init__(width="160px")
        self.definition = definition

    def validate(self, response, **kwargs):
        validation = super().validate(response, **kwargs)
        if validation is not None:
            self._record_validation_failure(**kwargs)
            return validation

        prediction = float(response.answer)
        if not math.isfinite(prediction):
            self._record_validation_failure(**kwargs)
            return FailedValidation(_("Please enter a finite number."))

        if prediction < self.definition["t_past"]:
            self._record_validation_failure(**kwargs)
            return FailedValidation(
                _("Your prediction must be at least {T_PAST} {UNIT}.").format(
                    T_PAST=self.definition["t_past"],
                    UNIT=unit_label(self.definition["unit"], self.definition["t_past"]),
                )
            )

        return None

    def _record_validation_failure(self, **kwargs):
        participant = kwargs.get("participant")
        if participant is None:
            return
        key = "validation_failures_" + trial_key(self.definition)
        participant.var.set(key, participant.var.get(key, default=0) + 1)

    def get_bot_response(self, experiment, bot, page, prompt):
        return prediction_for_bot(self.definition, active_locale(), bot.id)


class PredictionTrial(StaticTrial):
    time_estimate = 12

    def finalize_definition(self, definition, experiment, participant):
        definition = definition.copy()
        definition["displayed_locale"] = active_locale()
        definition["vignette_id"] = definition["category"]
        return definition

    def show_trial(self, experiment, participant):
        locale = active_locale()
        direction = "rtl" if is_rtl_locale(locale) else "ltr"
        unit = unit_label(self.definition["unit"], self.definition["t_past"])
        prompt = tags.div(
            tags.p(
                _("Question {POSITION} of 5").format(POSITION=self.position + 1),
                cls="progress-note",
            ),
            tags.h3(category_title(self.definition["category"])),
            tags.p(vignette(self.definition)),
            tags.p(
                _("Observed so far: {T_PAST} {UNIT}.").format(
                    T_PAST=self.definition["t_past"],
                    UNIT=unit,
                ),
                tags.br(),
                _("Please enter your intuitive prediction for the total value."),
            ),
            dir=direction,
            style="max-width: 760px; margin: 0 auto; text-align: {ALIGN};".format(
                ALIGN="right" if direction == "rtl" else "left"
            ),
        )
        return ModularPage(
            "prediction_" + self.definition["category"],
            prompt,
            PredictionControl(self.definition),
            time_estimate=self.time_estimate,
        )

    def format_answer(self, raw_answer, **kwargs):
        participant = kwargs.get("participant")
        metadata = kwargs.get("metadata") or {}
        prediction = float(raw_answer)
        validation_key = "validation_failures_" + trial_key(self.definition)
        validation_failures = (
            participant.var.get(validation_key, default=0) if participant is not None else 0
        )
        return {
            "category": self.definition["category"],
            "vignette_id": self.definition["vignette_id"],
            "t_past": self.definition["t_past"],
            "unit": self.definition["unit"],
            "displayed_locale": self.definition["displayed_locale"],
            "prediction": prediction,
            "prediction_is_finite": math.isfinite(prediction),
            "reaction_time": metadata.get("time_taken"),
            "validation_failures": validation_failures,
            "bot_profile": "locale_" + self.definition["displayed_locale"],
        }

    def score_answer(self, answer, definition):
        return 1.0 if answer["prediction_is_finite"] and answer["prediction"] >= definition["t_past"] else 0.0


nodes = [
    StaticNode(
        definition={
            "category": category,
            "t_past": t_past,
            "unit": params["unit"],
        },
        block=category,
    )
    for category, params in CATEGORIES.items()
    for t_past in params["t_past_values"]
]


trial_maker = StaticTrialMaker(
    id_="everyday_predictions",
    trial_class=PredictionTrial,
    nodes=nodes,
    expected_trials_per_participant=5,
    max_trials_per_participant=5,
    max_trials_per_block=1,
    allow_repeated_nodes=False,
    balance_across_nodes=True,
    check_performance_at_end=True,
    target_n_participants=18,
    target_trials_per_node=None,
    recruit_mode="n_participants",
)


def introduction_page():
    locale = active_locale()
    direction = "rtl" if is_rtl_locale(locale) else "ltr"
    return InfoPage(
        tags.div(
            tags.h2(_("Predicting everyday futures")),
            tags.p(
                _(
                    "Each question asks you to predict a duration or quantity from a single piece of information."
                )
            ),
            tags.p(
                _(
                    "Please read each question and enter your prediction in the box below it. We are interested in your intuitions, so please do not make complicated calculations."
                )
            ),
            tags.p(_("You will answer one question from each of five everyday categories.")),
            dir=direction,
            style="max-width: 760px; margin: 0 auto; text-align: {ALIGN};".format(
                ALIGN="right" if direction == "rtl" else "left"
            ),
        ),
        time_estimate=10,
    )


def debrief_page():
    locale = active_locale()
    direction = "rtl" if is_rtl_locale(locale) else "ltr"
    return InfoPage(
        tags.div(
            tags.h2(_("Thank you")),
            tags.p(
                _(
                    "This study concerns how people make everyday predictions under uncertainty from limited information."
                )
            ),
            tags.p(_("Your responses have been recorded.")),
            dir=direction,
            style="max-width: 760px; margin: 0 auto; text-align: {ALIGN};".format(
                ALIGN="right" if direction == "rtl" else "left"
            ),
        ),
        time_estimate=5,
    )


def record_locale(participant):
    participant.var.set("locale", active_locale())


class Exp(psynet.experiment.Experiment):
    label = "Predicting the Future Across Cultures"
    test_n_bots = 18

    config = {
        "locale": os.environ.get("PSYNET_LOCALE", "en"),
        "supported_locales": ["en", "it", "he"],
    }

    timeline = Timeline(
        NoConsent(),
        CodeBlock(record_locale),
        introduction_page(),
        trial_maker,
        debrief_page(),
    )

    def test_check_bot(self, participant):
        trials = participant.all_trials
        assert len(trials) == 5
        categories = {trial.answer["category"] for trial in trials}
        assert categories == set(CATEGORIES)
        for trial in trials:
            answer = trial.answer
            assert answer["displayed_locale"] == active_locale()
            assert answer["prediction_is_finite"]
            assert answer["prediction"] >= answer["t_past"]
            assert answer["reaction_time"] is not None
