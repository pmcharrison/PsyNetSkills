from pathlib import Path
from zipfile import ZipFile

import psynet.experiment
from markupsafe import Markup
from psynet.bot import BotResponse
from psynet.consent import MainConsent
from psynet.page import InfoPage, UnityPage
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

EXPERIMENT_DIR = Path(__file__).resolve().parent
UNITY_ZIP = EXPERIMENT_DIR / "static" / "ferry-market-webgl.zip"
UNITY_SCRIPTS_DIR = EXPERIMENT_DIR / "static" / "scripts"


def ensure_unity_build() -> None:
    """Extract the provided Unity WebGL build into PsyNet's static layout."""
    loader = UNITY_SCRIPTS_DIR / "Build" / "WebGL.loader.js"
    if loader.exists():
        return
    if not UNITY_ZIP.exists():
        raise FileNotFoundError(f"Missing Unity WebGL archive: {UNITY_ZIP}")
    UNITY_SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    with ZipFile(UNITY_ZIP) as archive:
        for member in archive.infolist():
            name = member.filename
            if name.startswith("__MACOSX/") or name.endswith("/") or "/._" in name:
                continue
            target = (UNITY_SCRIPTS_DIR / name).resolve()
            if not target.is_relative_to(UNITY_SCRIPTS_DIR.resolve()):
                raise ValueError(f"Unexpected path in Unity archive: {name}")
            archive.extract(member, UNITY_SCRIPTS_DIR)


ensure_unity_build()


def ferry_market_contents():
    return {
        # The Unity code names this field "speed", but the values are
        # travel delays; lower values are faster ferries.
        "ferry_speeds": [2, 2, 2],
        "ferry_tickets": [3, 3, 3],
        "Island_colors": ["red", "yellow", "green"],
        "ferry_ratings": [-1] * 9,
        "ferry_window_ratings": [-1] * 9,
        "ferry_trend_slope": [0.0] * 9,
        "ferry_popularity": [0] * 9,
        "dashboard_mode": "off",
        "show_dashboard": False,
        "show_stars": False,
        "show_speeds": False,
        "show_popularity": False,
        "show_window_stars": False,
        "show_trend_arrow": False,
    }


class FerryMarketUnityPage(UnityPage):
    def __init__(self, contents, **kwargs):
        super().__init__(
            title="Unity - FerryGov",
            resources="/static",
            contents=contents,
            session_id="0",
            game_container_width="960px",
            game_container_height="600px",
            time_estimate=120,
            **kwargs,
        )

    def format_answer(self, raw_answer, **kwargs):
        if raw_answer is None:
            raw_answer = {}
        if isinstance(raw_answer, dict):
            return raw_answer
        return {"raw_answer": raw_answer}

    def get_bot_response(self, experiment, bot):
        return BotResponse(
            answer={
                "ferryChoice": 0,
                "FeedbackScore": 5,
                "FeedbackDelivered": True,
                "increment_speed": 0,
                "ferry": 0,
                "ferry_ticket": 3,
                "ferry_speed": 2,
                "reward": 100,
                "toll": 30,
                "balance": 0,
                "coins": [],
                "timeElapsed": 20.0,
                "calledFerryTime": 5.0,
                "crossedFinishLineTime": 7.0,
                "feedbackRequestTime": 12.0,
                "feedbackRequested": True,
                "scoreActive": True,
                "participating": True,
                "expire": False,
                "turbo": False,
                "answer": "5",
                "version": 2,
                "bot_simulated": True,
            }
        )


class FerryMarketTrial(StaticTrial):
    accumulate_answers = False
    time_estimate = 120

    def show_trial(self, experiment, participant):
        contents = ferry_market_contents()
        contents["island_index"] = self.node.definition["island_index"]
        return FerryMarketUnityPage(contents=contents, time_estimate=self.time_estimate)


trial_maker = StaticTrialMaker(
    id_="ferry_market_unity",
    trial_class=FerryMarketTrial,
    nodes=[
        StaticNode(definition={"island_index": i})
        for i in range(1, 4)
    ],
    max_trials_per_participant=3,
    expected_trials_per_participant=3,
    allow_repeated_nodes=False,
    balance_across_nodes=False,
    check_performance_at_end=False,
    check_performance_every_trial=False,
    target_n_participants=1,
    recruit_mode="n_participants",
)


class Exp(psynet.experiment.Experiment):
    label = "Ferry Market Unity"
    test_n_bots = 1

    timeline = Timeline(
        MainConsent(time_estimate=30),
        InfoPage(
            Markup(
                """
                <h3>Ferry Market</h3>
                <p>You will play a Unity WebGL game called <strong>Ferry Market</strong>.</p>
                <p>Click inside the game canvas, then use the arrow keys to move forward and sideways. Use the in-game buttons and objects to complete the task.</p>
                <p>The experiment will continue automatically after the game reports completion.</p>
                """
            ),
            time_estimate=15,
        ),
        trial_maker,
        InfoPage("Thank you. You have finished the Ferry Market task.", time_estimate=5),
    )
