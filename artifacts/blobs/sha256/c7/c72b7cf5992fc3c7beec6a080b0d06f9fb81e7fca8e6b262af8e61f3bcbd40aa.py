# pylint: disable=abstract-method,unused-argument

from __future__ import annotations

import json
from collections import Counter
from html import escape
from pathlib import Path

import pandas as pd
from markupsafe import Markup

import psynet.experiment
from psynet.modular_page import KeyboardPushButtonControl, ModularPage
from psynet.page import InfoPage, WaitPage
from psynet.participant import Participant
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "stimuli" / "manifest.json"
IMAGE_BASE_URL = "/static/stimuli"


def load_stimuli() -> list[dict]:
    return json.loads(MANIFEST_PATH.read_text())


STIMULI = load_stimuli()

nodes = [
    StaticNode(definition=stimulus, block="main")
    for stimulus in STIMULI
]


CARD_CSS = """
body {
    background: linear-gradient(135deg, #fff5f7 0%, #f0f4ff 100%);
}
.aesthetic-card {
    width: min(92vw, 560px);
    margin: 0 auto 18px;
    padding: 22px 22px 18px;
    border-radius: 34px;
    background: #ffffff;
    box-shadow: 0 24px 60px rgba(31, 41, 55, 0.18);
    text-align: center;
}
.aesthetic-card img {
    width: 500px;
    height: 500px;
    max-width: 100%;
    object-fit: cover;
    border-radius: 26px;
    display: block;
    margin: 0 auto 16px;
}
.aesthetic-card h2 {
    margin: 0 0 6px;
    font-weight: 800;
    letter-spacing: -0.02em;
}
.aesthetic-card p {
    margin: 4px 0;
}
.swipe-help {
    color: #667085;
    font-size: 1.05rem;
}
.push-button-container {
    gap: 18px;
}
.push-button {
    min-width: 150px !important;
    border-radius: 999px !important;
    font-weight: 700 !important;
    pointer-events: none;
}
.feedback-card {
    width: min(90vw, 520px);
    margin: 80px auto 0;
    padding: 42px;
    border-radius: 30px;
    background: white;
    text-align: center;
    box-shadow: 0 24px 60px rgba(31, 41, 55, 0.18);
}
.feedback-card .feedback-word {
    font-size: 4rem;
    font-weight: 900;
    line-height: 1;
}
.feedback-card.like .feedback-word {
    color: #16a34a;
}
.feedback-card.dislike .feedback-word {
    color: #dc2626;
}
"""


def validate_arrow_keycode(code: str) -> bool:
    return code in {"ArrowLeft", "ArrowRight"}


def response_direction(response: str) -> str:
    return {"dislike": "left", "like": "right"}[response]


class AestheticTrial(StaticTrial):
    time_estimate = 3.5

    def show_trial(self, experiment, participant):
        definition = self.definition
        image_url = f"{IMAGE_BASE_URL}/{definition['filename']}"
        category = definition["category"].replace("_", " ")
        prompt = Markup(
            f"""
            <div class="aesthetic-card">
                <img src="{image_url}" alt="{escape(definition['image_id'])}">
                <h2>Do you like this image?</h2>
                <p class="swipe-help">
                    Press <kbd>Left arrow</kbd> for Dislike or
                    <kbd>Right arrow</kbd> for Like.
                </p>
                <p><small>Category: {escape(category.title())}</small></p>
            </div>
            """
        )
        return ModularPage(
            "aesthetic_image_trial",
            prompt,
            KeyboardPushButtonControl(
                choices=["dislike", "like"],
                labels=["<kbd>&larr;</kbd> Dislike", "Like <kbd>&rarr;</kbd>"],
                keys=["ArrowLeft", "ArrowRight"],
                validate_keycode=validate_arrow_keycode,
                arrange_vertically=False,
                style="min-width: 150px; margin: 8px;",
            ),
            time_estimate=self.time_estimate,
            css=CARD_CSS,
        )

    def format_answer(self, raw_answer):
        liked = raw_answer == "like"
        return {
            "image_id": self.definition["image_id"],
            "category": self.definition["category"],
            "source_metadata": {
                "source_title": self.definition["source_title"],
                "source_page": self.definition["source_page"],
                "source_image_url": self.definition["source_image_url"],
                "license": self.definition["license"],
                "artist": self.definition["artist"],
                "credit": self.definition["credit"],
            },
            "response_direction": response_direction(raw_answer),
            "response": "Like" if liked else "Dislike",
            "liked": liked,
            "response_time_seconds": self.time_taken,
        }

    def show_feedback(self, experiment, participant):
        response = self.answer["response"]
        kind = response.lower()
        return WaitPage(
            wait_time=0.55,
            content=Markup(
                f"""
                <div class="feedback-card {kind}">
                    <div class="feedback-word">{response}</div>
                </div>
                <style>{CARD_CSS}</style>
                """
            ),
        )


trial_maker = StaticTrialMaker(
    id_="aesthetic_preferences",
    trial_class=AestheticTrial,
    nodes=nodes,
    expected_trials_per_participant="n_nodes",
    max_trials_per_participant="n_nodes",
    allow_repeated_nodes=False,
    balance_across_nodes=True,
    check_performance_at_end=False,
    check_performance_every_trial=False,
    recruit_mode="n_participants",
    target_n_participants=1,
)


class Exp(psynet.experiment.Experiment):
    label = "Aesthetics Tinder"
    test_n_bots = 2

    timeline = Timeline(
        InfoPage(
            Markup(
                """
                <h2>Aesthetics Tinder</h2>
                <p>You will see 15 real-world images, one at a time.</p>
                <p>
                    Press <kbd>Left arrow</kbd> if you <strong>dislike</strong>
                    the image, or press <kbd>Right arrow</kbd> if you
                    <strong>like</strong> it.
                </p>
                <p>Please answer each image from your first impression.</p>
                """
            ),
            time_estimate=10,
        ),
        trial_maker,
        InfoPage(
            Markup(
                """
                <h2>All done!</h2>
                <p>Thank you for rating the image set.</p>
                """
            ),
            time_estimate=5,
        ),
    )

    def test_check_bot(self, participant):
        trials = [
            trial
            for trial in participant.all_trials
            if isinstance(trial, StaticTrial)
        ]
        assert len(trials) == len(STIMULI)
        assert Counter(trial.definition["category"] for trial in trials) == {
            "clothes": 5,
            "house_interiors": 5,
            "paintings": 5,
        }
        assert all(trial.answer["response"] in {"Like", "Dislike"} for trial in trials)
        assert all(trial.answer["response_time_seconds"] is not None for trial in trials)

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trial_rows = []
        for trial in StaticTrial.query.all():
            if not trial.definition or "image_id" not in trial.definition:
                continue
            answer = trial.answer or {}
            source_metadata = answer.get("source_metadata") or {}
            trial_rows.append(
                {
                    "trial_id": trial.id,
                    "participant_id": trial.participant_id,
                    "image_id": trial.definition["image_id"],
                    "category": trial.definition["category"],
                    "source_title": source_metadata.get("source_title"),
                    "source_page": source_metadata.get("source_page"),
                    "source_image_url": source_metadata.get("source_image_url"),
                    "source_license": source_metadata.get("license"),
                    "source_artist": source_metadata.get("artist"),
                    "source_credit": source_metadata.get("credit"),
                    "response_direction": answer.get("response_direction"),
                    "response": answer.get("response"),
                    "liked": answer.get("liked"),
                    "response_time_seconds": answer.get("response_time_seconds"),
                }
            )
        participant_rows = [
            {
                "participant_id": participant.id,
                "status": participant.status,
                "n_trials": len(participant.all_trials),
            }
            for participant in Participant.query.all()
        ]
        return {
            "trial": pd.DataFrame.from_records(trial_rows),
            "participant": pd.DataFrame.from_records(participant_rows),
        }
