"""Generated-tone tapping rhythm experiment for PsyNetSkills."""

from __future__ import annotations

import json
import math
import random
import struct
import wave
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, pstdev

import psynet.experiment
from markupsafe import Markup
from psynet.asset import asset
from psynet.bot import Bot, BotDriver, BotResponse
from psynet.consent import NoConsent
from psynet.db import transaction
from psynet.modular_page import AudioPrompt, ModularPage, PushButtonControl, TimedPushButtonControl
from psynet.page import InfoPage, SuccessfulEndPage, UnsuccessfulEndPage
from psynet.timeline import CodeBlock, Timeline, conditional, join
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

BASE_DIR = Path(__file__).parent
MANIFEST_PATH = BASE_DIR / "stimuli" / "manifest.json"
SAMPLE_RATE = 44_100
PRE_ROLL_SECONDS = 0.8
POST_ROLL_SECONDS = 0.8
CLICK_DURATION_SECONDS = 0.045
MIN_CALIBRATION_TAPS = 4
TEMPO_TOLERANCE_SECONDS = 0.14
MAX_ITI_SD_SECONDS = 0.12
PROFILES = ["good", "too-few-taps", "off-tempo", "noisy", "dropout"]
MAIN_TRIALS_PER_PARTICIPANT = 3

STIMULUS_SPECS = [
    {"stimulus_id": "calibration_100bpm", "trial_kind": "calibration", "condition": "calibration", "tempo_bpm": 100, "beats": 5, "accent_every": None, "filename": "calibration_100bpm.wav"},
    {"stimulus_id": "main_slow_90bpm", "trial_kind": "main", "condition": "slow_isochronous", "tempo_bpm": 90, "beats": 6, "accent_every": None, "filename": "main_slow_90bpm.wav"},
    {"stimulus_id": "main_medium_120bpm", "trial_kind": "main", "condition": "medium_isochronous", "tempo_bpm": 120, "beats": 7, "accent_every": None, "filename": "main_medium_120bpm.wav"},
    {"stimulus_id": "main_accented_110bpm", "trial_kind": "main", "condition": "accented_every_two", "tempo_bpm": 110, "beats": 7, "accent_every": 2, "filename": "main_accented_110bpm.wav"},
]


def synth_click_track(path: Path, *, tempo_bpm: int, beats: int, accent_every: int | None = None):
    """Create a deterministic monophonic metronome WAV."""
    ioi = 60.0 / tempo_bpm
    duration = PRE_ROLL_SECONDS + (beats - 1) * ioi + CLICK_DURATION_SECONDS + POST_ROLL_SECONDS
    n_samples = int(math.ceil(duration * SAMPLE_RATE))
    samples = [0.0] * n_samples
    for beat in range(beats):
        onset = PRE_ROLL_SECONDS + beat * ioi
        frequency = 880.0 if accent_every and beat % accent_every == 0 else 660.0
        amplitude = 0.65 if accent_every and beat % accent_every == 0 else 0.5
        start = int(onset * SAMPLE_RATE)
        length = int(CLICK_DURATION_SECONDS * SAMPLE_RATE)
        for i in range(length):
            idx = start + i
            if idx >= n_samples:
                break
            envelope = 1.0 - (i / max(1, length - 1))
            samples[idx] += amplitude * envelope * math.sin(2 * math.pi * frequency * i / SAMPLE_RATE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        frames = b"".join(struct.pack("<h", max(-32767, min(32767, int(s * 32767)))) for s in samples)
        wav.writeframes(frames)
    return duration, ioi


def write_manifest(path: Path = MANIFEST_PATH):
    stimuli = []
    for spec in STIMULUS_SPECS:
        stimulus = dict(spec)
        duration, ioi = synth_click_track(path.parent / stimulus["filename"], tempo_bpm=stimulus["tempo_bpm"], beats=stimulus["beats"], accent_every=stimulus["accent_every"])
        stimulus.update({
            "pre_roll_seconds": PRE_ROLL_SECONDS,
            "post_roll_seconds": POST_ROLL_SECONDS,
            "click_duration_seconds": CLICK_DURATION_SECONDS,
            "beat_interval_seconds": round(ioi, 6),
            "duration_seconds": round(duration, 6),
        })
        stimuli.append(stimulus)
    path.write_text(json.dumps({"stimuli": stimuli, "timing_constants": {"sample_rate": SAMPLE_RATE, "pre_roll_seconds": PRE_ROLL_SECONDS, "post_roll_seconds": POST_ROLL_SECONDS, "click_duration_seconds": CLICK_DURATION_SECONDS}}, indent=2) + "\n", encoding="utf-8")


def load_manifest():
    if not MANIFEST_PATH.exists():
        write_manifest(MANIFEST_PATH)
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["stimuli"]


def parse_psynet_time(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def seconds_after_prompt_start(event_log):
    prompt_start = next((event for event in event_log if event.get("eventType") == "promptStart"), None)
    if prompt_start is None:
        return []
    start = parse_psynet_time(prompt_start["localTime"])
    onsets = []
    for event in event_log:
        if event.get("eventType") == "pushButtonClicked":
            onsets.append(round((parse_psynet_time(event["localTime"]) - start).total_seconds(), 4))
    return onsets


def inter_tap_intervals(onsets):
    return [round(b - a, 4) for a, b in zip(onsets, onsets[1:])]


def summarize_tapping(onsets, definition, profile_id):
    intervals = inter_tap_intervals(onsets)
    n_taps = len(onsets)
    mean_iti = round(mean(intervals), 4) if intervals else None
    sd_iti = round(pstdev(intervals), 4) if len(intervals) > 1 else 0.0 if intervals else None
    target_ioi = float(definition["beat_interval_seconds"])
    tempo_error = round(mean_iti - target_ioi, 4) if mean_iti is not None else None

    failure_reason = None
    if profile_id == "dropout":
        failure_reason = "dropout_no_taps"
    elif n_taps < MIN_CALIBRATION_TAPS:
        failure_reason = "too_few_taps"
    elif mean_iti is None or abs(mean_iti - target_ioi) > TEMPO_TOLERANCE_SECONDS:
        failure_reason = "off_tempo"
    elif sd_iti is not None and sd_iti > MAX_ITI_SD_SECONDS:
        failure_reason = "noisy_tapping"

    failed = failure_reason is not None
    calibration_status = "failed" if definition["trial_kind"] == "calibration" and failed else "passed" if definition["trial_kind"] == "calibration" else "not_applicable"
    return {
        "stimulus_id": definition["stimulus_id"],
        "trial_kind": definition["trial_kind"],
        "condition": definition["condition"],
        "audio_filename": definition["filename"],
        "tempo_bpm": definition["tempo_bpm"],
        "beat_interval_seconds": target_ioi,
        "duration_seconds": definition["duration_seconds"],
        "pre_roll_seconds": definition["pre_roll_seconds"],
        "post_roll_seconds": definition["post_roll_seconds"],
        "tap_onsets": onsets,
        "inter_tap_intervals": intervals,
        "n_taps": n_taps,
        "mean_iti_seconds": mean_iti,
        "sd_iti_seconds": sd_iti,
        "tempo_error_seconds": tempo_error,
        "calibration_status": calibration_status,
        "failed": failed,
        "failure_reason": failure_reason,
        "dropout": profile_id == "dropout",
        "simulated_profile_id": profile_id,
    }


def profile_tap_onsets(profile_id, definition):
    target = float(definition["beat_interval_seconds"])
    beats = int(definition["beats"])
    if profile_id == "dropout":
        return []
    if profile_id == "too-few-taps":
        beats = 2
    if profile_id == "off-tempo":
        target *= 1.35
    offsets = [0.0] * beats
    if profile_id == "good":
        offsets = [0.0, 0.018, -0.012, 0.011, -0.016, 0.007, -0.004][:beats]
    elif profile_id == "noisy":
        offsets = [0.0, 0.24, -0.18, 0.31, -0.22, 0.19, -0.26][:beats]
    return [round(PRE_ROLL_SECONDS + i * target + offsets[i], 4) for i in range(beats)]


def event_log_from_onsets(onsets):
    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    def stamp(seconds):
        return (base + timedelta(seconds=seconds)).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    events = [
        {"eventType": "trialConstruct", "localTime": stamp(-0.010), "info": None},
        {"eventType": "trialPrepare", "localTime": stamp(-0.005), "info": None},
        {"eventType": "trialStart", "localTime": stamp(0.000), "info": None},
        {"eventType": "promptStart", "localTime": stamp(0.000), "info": None},
        {"eventType": "responseEnable", "localTime": stamp(0.000), "info": None},
        {"eventType": "submitEnable", "localTime": stamp(0.000), "info": None},
    ]
    for onset in onsets:
        events.append({"eventType": "pushButtonClicked", "localTime": stamp(onset), "info": {"buttonId": "tap"}})
    return events


class TapButtonControl(TimedPushButtonControl):
    def __init__(self, definition):
        super().__init__(
            choices=["tap"],
            labels=["Tap beat"],
            arrange_vertically=True,
            button_highlight_duration=0.12,
            style="font-size: 28px; min-width: 220px; min-height: 90px; margin: 20px;",
        )
        self.definition = definition

    def format_answer(self, raw_answer, **kwargs):
        participant = kwargs["participant"]
        event_log = kwargs["metadata"].get("event_log", [])
        profile_id = participant.var.get("simulated_profile_id", default="browser-participant")
        return summarize_tapping(seconds_after_prompt_start(event_log), self.definition, profile_id)

    def get_bot_response(self, experiment, bot, page, prompt):
        profile_id = bot.var.get("simulated_profile_id", default="good")
        onsets = profile_tap_onsets(profile_id, self.definition)
        return BotResponse(raw_answer=None, metadata={"event_log": event_log_from_onsets(onsets)})


class TappingTrial(StaticTrial):
    time_estimate = 10

    def show_trial(self, experiment, participant):
        definition = self.definition
        prompt_text = Markup(
            f"""
            <div style='text-align:center; max-width: 760px; margin: auto;'>
              <h3>{'Calibration' if definition['trial_kind'] == 'calibration' else 'Main tapping trial'}</h3>
              <p>Wait for the clicks, tap the large button in time with each beat, then press Next.</p>
              <p><strong>Condition:</strong> {definition['condition']} &middot; <strong>Tempo:</strong> {definition['tempo_bpm']} BPM</p>
            </div>
            """
        )
        page = ModularPage(
            f"tap_{definition['stimulus_id']}",
            prompt=AudioPrompt(audio=self.assets["stimulus_audio"], text=prompt_text, controls=False),
            control=TapButtonControl(definition),
            time_estimate=self.time_estimate,
            save_answer="last_tap_response",
            start_trial_automatically=False,
            show_start_button=True,
        )
        if definition["trial_kind"] == "calibration":
            return join(page, CodeBlock(save_calibration_result))
        return page


class VolumeCheckTrial(StaticTrial):
    time_estimate = 8

    def show_trial(self, experiment, participant):
        return ModularPage(
            "volume_check",
            prompt=AudioPrompt(
                audio=self.assets["stimulus_audio"],
                text="Play the sample click track and set a comfortable listening volume.",
                controls={"Play": "Play volume-check clicks"},
            ),
            control=PushButtonControl(
                ["I can hear the clicks"], bot_response="I can hear the clicks"
            ),
            time_estimate=self.time_estimate,
        )


def save_calibration_result(participant):
    response = participant.var.get("last_tap_response")
    passed = bool(response and response.get("calibration_status") == "passed")
    participant.var.set("calibration_passed", passed)
    participant.var.set("calibration_failure_reason", None if passed else response.get("failure_reason") if response else "missing_calibration_response")


def ensure_profile_metadata(participant):
    if not participant.var.has("simulated_profile_id"):
        participant.var.set("simulated_profile_id", "browser-participant")
    participant.var.set("simulated_profile_group", participant.var.get("simulated_profile_id"))


def make_nodes(kind):
    return [
        StaticNode(
            definition=stimulus,
            assets={"stimulus_audio": asset(str(Path("stimuli") / stimulus["filename"]), cache=False)},
        )
        for stimulus in load_manifest()
        if stimulus["trial_kind"] == kind
    ]


volume_check_trials = StaticTrialMaker(
    id_="volume_check",
    trial_class=VolumeCheckTrial,
    nodes=[
        StaticNode(
            definition={
                "stimulus_id": "volume_check_100bpm",
                "trial_kind": "volume_check",
                "condition": "volume_check",
            },
            assets={
                "stimulus_audio": asset(
                    str(Path("stimuli") / "calibration_100bpm.wav"), cache=False
                )
            },
        )
    ],
    expected_trials_per_participant=1,
    max_trials_per_participant=1,
    target_n_participants=len(PROFILES),
    recruit_mode="n_participants",
)


calibration_trials = StaticTrialMaker(
    id_="tapping_calibration",
    trial_class=TappingTrial,
    nodes=make_nodes("calibration"),
    expected_trials_per_participant=1,
    max_trials_per_participant=1,
    target_n_participants=len(PROFILES),
    recruit_mode="n_participants",
)

main_trials = StaticTrialMaker(
    id_="main_tapping_trials",
    trial_class=TappingTrial,
    nodes=make_nodes("main"),
    expected_trials_per_participant=MAIN_TRIALS_PER_PARTICIPANT,
    max_trials_per_participant=MAIN_TRIALS_PER_PARTICIPANT,
    target_n_participants=1,
    recruit_mode="n_participants",
)


class Exp(psynet.experiment.Experiment):
    label = "Generated tapping rhythm experiment"
    test_n_bots = len(PROFILES)
    test_time_factor = 0.05

    timeline = Timeline(
        NoConsent(),
        CodeBlock(ensure_profile_metadata),
        InfoPage(
            Markup(
                """
                <h2>Tap along to generated metronome clicks</h2>
                <p>This public-safe demo uses only generated tones. Tap the on-screen button in time with the beat.</p>
                <p>No microphone recording, private data, real recruitment credentials, or copyrighted audio are used.</p>
                """
            ),
            time_estimate=8,
        ),
        volume_check_trials,
        calibration_trials,
        conditional(
            "calibration_gate",
            condition=lambda participant: participant.var.get("calibration_passed", default=False),
            logic_if_true=join(
                InfoPage("Calibration recorded usable tapping. The main trials will now begin.", time_estimate=4),
                main_trials,
                SuccessfulEndPage(),
            ),
            logic_if_false=join(
                InfoPage(
                    "The calibration did not record usable tapping, so this demo exits before the main task.",
                    time_estimate=4,
                ),
                UnsuccessfulEndPage(),
            ),
        ),
    )

    def initialize_bot(self, bot):
        bot.var.set("simulated_profile_id", "pending-profile")
        bot.var.set("simulated_profile_group", "pending-profile")

    @classmethod
    def run_bot(cls, bot: BotDriver = None, render_pages: bool = True, time_factor: float = 0.0):
        if bot is None:
            bot = BotDriver()
        profile = PROFILES[(bot.id - 1) % len(PROFILES)]
        with transaction():
            participant = Bot.query.get(bot.id)
            participant.var.set("simulated_profile_id", profile)
            participant.var.set("simulated_profile_group", profile)
        bot.take_experiment(render_pages, time_factor)

    def test_check_bot(self, bot: Bot, **kwargs):
        profile = bot.var.get("simulated_profile_id")
        assert profile in PROFILES
        calibration = [trial for trial in bot.all_trials if trial.definition["trial_kind"] == "calibration"]
        assert len(calibration) == 1
        calibration_answer = calibration[0].answer
        assert calibration_answer["simulated_profile_id"] == profile
        if profile == "good":
            assert not bot.failed
            assert bot.complete
            assert calibration_answer["calibration_status"] == "passed"
            main = [trial for trial in bot.all_trials if trial.definition["trial_kind"] == "main"]
            assert len(main) == MAIN_TRIALS_PER_PARTICIPANT
            assert all(not trial.answer["failed"] for trial in main)
        else:
            assert bot.failed
            assert calibration_answer["failed"]
            assert calibration_answer["failure_reason"] is not None
            main = [trial for trial in bot.all_trials if trial.definition["trial_kind"] == "main"]
            assert len(main) == 0
            if profile == "dropout":
                assert calibration_answer["dropout"]
