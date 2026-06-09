from __future__ import annotations

import json
import random
from pathlib import Path

import pandas as pd
from markupsafe import Markup

import psynet.experiment
from psynet.asset import asset
from psynet.bot import Bot
from psynet.modular_page import KeyboardPushButtonControl, ModularPage
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.timeline import Page, Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

ROOT = Path(__file__).parent
MANIFEST_PATH = ROOT / "data" / "stimuli_manifest.json"
PREFERENCE_LABELS = {
    "dislike": {"label": "Dislike", "direction": "left", "color": "#c62828"},
    "like": {"label": "Like", "direction": "right", "color": "#2e7d32"},
}


def load_stimuli() -> list[dict]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def get_nodes() -> list[StaticNode]:
    nodes = []
    for stimulus in load_stimuli():
        nodes.append(
            StaticNode(
                definition={
                    key: stimulus[key]
                    for key in [
                        "stimulus_id",
                        "category",
                        "source_title",
                        "source_page",
                        "source_request_url",
                        "image_url",
                        "author",
                        "license",
                        "license_url",
                        "width_px",
                        "height_px",
                    ]
                },
                assets={
                    "image": asset(ROOT / stimulus["path"], extension=".jpg", cache=True),
                },
            )
        )
    return nodes


def validate_arrow_key(key: str) -> bool:
    return key in {"ArrowLeft", "ArrowRight"}


class PreferenceFeedbackPage(Page):
    def __init__(self, text: str, color: str):
        super().__init__(
            label="preference_feedback",
            time_estimate=0.7,
            save_answer=False,
            template_str="""
            {% extends "timeline-page.html" %}
            {% block main_body %}
                <div style="min-height: 70vh; display: flex; align-items: center; justify-content: center; background: #fff;">
                    <div style="font-size: 4.5rem; font-weight: 800; color: {{ color }};">
                        {{ text }}
                    </div>
                </div>
            {% endblock %}
            {% block scripts %}
                {{ super() }}
                <script>
                    setTimeout(function () {
                        psynet.nextPage();
                    }, 700);
                </script>
            {% endblock %}
            """,
            template_arg={"text": text, "color": color},
        )


class AestheticImageTrial(StaticTrial):
    time_estimate = 4

    def show_trial(self, experiment, participant):
        category = self.definition["category"].replace("_", " ")
        return ModularPage(
            "aesthetic_image_trial",
            Markup(
                f"""
                <style>
                    .swipe-wrap {{
                        display: flex;
                        justify-content: center;
                        margin: 12px 0 22px;
                    }}
                    .swipe-card {{
                        width: 540px;
                        max-width: 92vw;
                        padding: 20px;
                        border-radius: 28px;
                        background: #fff;
                        box-shadow: 0 14px 40px rgba(0, 0, 0, 0.22);
                        text-align: center;
                    }}
                    .swipe-card img {{
                        width: 500px;
                        height: 500px;
                        max-width: 100%;
                        object-fit: cover;
                        border-radius: 20px;
                    }}
                    .swipe-category {{
                        margin-top: 14px;
                        color: #616161;
                        font-size: 0.9rem;
                        letter-spacing: 0.08em;
                        text-transform: uppercase;
                    }}
                    .swipe-instructions {{
                        font-size: 1.05rem;
                    }}
                    .key-hint {{
                        display: inline-block;
                        margin: 0 10px;
                    }}
                </style>
                <p class="swipe-instructions">
                    Do you like this image?
                    <span class="key-hint"><kbd>&larr;</kbd> Dislike</span>
                    <span class="key-hint"><kbd>&rarr;</kbd> Like</span>
                </p>
                <div class="swipe-wrap">
                    <div class="swipe-card">
                        <img src="{self.assets["image"].url}" alt="{self.definition["stimulus_id"]}">
                        <div class="swipe-category">{category}</div>
                    </div>
                </div>
                """
            ),
            KeyboardPushButtonControl(
                choices=["dislike", "like"],
                labels=["Dislike \u2190", "Like \u2192"],
                keys=["ArrowLeft", "ArrowRight"],
                validate_keycode=validate_arrow_key,
                arrange_vertically=False,
                show_next_button=False,
                bot_response=lambda: random.choice(["dislike", "like"]),
            ),
            time_estimate=self.time_estimate,
        )

    def format_answer(self, raw_answer, **kwargs):
        preference = PREFERENCE_LABELS[raw_answer]
        return {
            "response": preference["label"],
            "response_direction": preference["direction"],
            "raw_key_choice": raw_answer,
        }

    def show_feedback(self, experiment, participant):
        response = self.answer["response"]
        color = PREFERENCE_LABELS[self.answer["raw_key_choice"]]["color"]
        return PreferenceFeedbackPage(response, color)


trial_maker = StaticTrialMaker(
    id_="aesthetic_image_trials",
    trial_class=AestheticImageTrial,
    nodes=get_nodes,
    expected_trials_per_participant="n_nodes",
    max_trials_per_participant="n_nodes",
    allow_repeated_nodes=False,
    balance_across_nodes=False,
    check_performance_at_end=False,
    check_performance_every_trial=False,
    recruit_mode="n_trials",
    target_n_participants=None,
    target_trials_per_node=None,
)


class Exp(psynet.experiment.Experiment):
    label = "Aesthetics Tinder"
    test_n_bots = 2

    timeline = Timeline(
        InfoPage(
            Markup(
                """
                <h2>Aesthetic image preferences</h2>
                <p>
                    You will see 15 images, one at a time, in a card layout.
                    Use the <kbd>&larr;</kbd> left arrow key if you dislike the
                    image, and the <kbd>&rarr;</kbd> right arrow key if you like it.
                </p>
                <p>Please answer every image using only the arrow keys.</p>
                """
            ),
            time_estimate=8,
        ),
        trial_maker,
        InfoPage(
            Markup(
                """
                <h2>Thank you!</h2>
                <p>You have rated all 15 images.</p>
                """
            ),
            time_estimate=4,
        ),
    )

    def test_check_bot(self, bot: Bot, **kwargs):
        assert not bot.failed
        trials = bot.alive_trials
        assert len(trials) == 15
        assert {trial.definition["category"] for trial in trials} == {
            "clothes",
            "house_interiors",
            "paintings",
        }
        assert all(trial.definition["width_px"] == 500 for trial in trials)
        assert all(trial.definition["height_px"] == 500 for trial in trials)
        assert all(trial.answer["response"] in {"Like", "Dislike"} for trial in trials)
        assert all(
            trial.answer["response_direction"] in {"left", "right"} for trial in trials
        )

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trials = []
        for trial in AestheticImageTrial.query.all():
            answer = trial.answer or {}
            trials.append(
                {
                    "trial_id": trial.id,
                    "participant_id": trial.participant_id,
                    "stimulus_id": trial.definition.get("stimulus_id"),
                    "category": trial.definition.get("category"),
                    "source_title": trial.definition.get("source_title"),
                    "source_page": trial.definition.get("source_page"),
                    "source_request_url": trial.definition.get("source_request_url"),
                    "image_url": trial.definition.get("image_url"),
                    "author": trial.definition.get("author"),
                    "license": trial.definition.get("license"),
                    "license_url": trial.definition.get("license_url"),
                    "response_direction": answer.get("response_direction"),
                    "preference_response": answer.get("response"),
                    "raw_key_choice": answer.get("raw_key_choice"),
                    "response_time_sec": trial.time_taken,
                }
            )
        participants = [
            {"participant_id": participant.id, "status": participant.status}
            for participant in Participant.query.all()
        ]
        return {
            "trial": pd.DataFrame.from_records(trials),
            "participant": pd.DataFrame.from_records(participants),
        }


if __name__ == "__main__":
    stimuli = load_stimuli()
    print(f"Loaded {len(stimuli)} stimuli from {MANIFEST_PATH}")
    for stimulus in stimuli:
        print(
            f"- {stimulus['stimulus_id']}: {stimulus['category']} "
            f"({stimulus['width_px']} x {stimulus['height_px']})"
        )
