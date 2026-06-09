from pathlib import Path
from zipfile import ZipFile

import psynet.experiment
from markupsafe import Markup
from psynet.consent import MainConsent
from psynet.page import InfoPage, UnityPage
from psynet.timeline import Timeline

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


class FerryMarketUnityPage(UnityPage):
    def __init__(self, **kwargs):
        super().__init__(
            title="Ferry Market",
            resources="/static",
            contents={
                "game": "ferry-market",
                "completion_instruction": "Finish the Unity task to continue.",
            },
            session_id="ferry-market-unity",
            game_container_width="960px",
            game_container_height="600px",
            time_estimate=120,
            bot_response={
                "completed": True,
                "source": "psynet-bot-response",
            },
            **kwargs,
        )

    def format_answer(self, raw_answer, **kwargs):
        if raw_answer is None:
            raw_answer = {}
        if isinstance(raw_answer, dict):
            return raw_answer
        return {"raw_answer": raw_answer}


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
        FerryMarketUnityPage(),
        InfoPage("Thank you. You have finished the Ferry Market task.", time_estimate=5),
    )
