import json
import math
import os
import random
import tempfile
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from dallinger import db
from dallinger.config import get_config
from markupsafe import Markup
import requests
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

import psynet.experiment
from psynet.asset import asset
from psynet.bot import Bot, BotResponse
from psynet.data import SQLBase, SQLMixin, register_table
from psynet.demography.general import ExperimentFeedback
from psynet.modular_page import ModularPage, Prompt, PushButtonControl, SliderControl
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.process import AsyncProcess
from psynet.timeline import CodeBlock, Timeline
from psynet.trial.gibbs import GibbsNetwork, GibbsNode, GibbsTrial, GibbsTrialMaker
from psynet.trial.main import TrialNode
from psynet.utils import get_logger

logger = get_logger()

TARGETS = ["tree", "rock", "carrot", "banana"]
COLORS = ["red", "green", "blue"]
AI_PROMPT_TEMPLATE_VERSION = "gibbs-hybrid-v1"


@dataclass(frozen=True)
class HybridConfig:
    ai_participant_proportion: float
    target_n_participants: Optional[int]
    ai_scheduler_enabled: bool
    ai_scheduler_max_running_bots: int
    openrouter_api_key_env: str
    openrouter_model: str
    openrouter_base_url: str
    openrouter_timeout_seconds: float
    openrouter_max_retries: int
    openrouter_mock_mode: bool


@dataclass(frozen=True)
class HybridSchedulerState:
    human_count: int
    ai_count: int
    running_ai_count: int
    participant_target: Optional[int]
    trial_capacity_remaining: Optional[int] = None


def _coerce_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _optional_int(value):
    if value in {None, ""}:
        return None
    return int(value)


def var_get(obj, key, default=None):
    try:
        return getattr(obj.var, key)
    except (AttributeError, KeyError):
        return default


def read_hybrid_config(config=None) -> HybridConfig:
    if config is None:
        config = get_config()

    return HybridConfig(
        ai_participant_proportion=float(config.get("ai_participant_proportion", 0)),
        target_n_participants=_optional_int(config.get("target_n_participants", None)),
        ai_scheduler_enabled=_coerce_bool(config.get("ai_scheduler_enabled", False)),
        ai_scheduler_max_running_bots=int(
            config.get("ai_scheduler_max_running_bots", 4)
        ),
        openrouter_api_key_env=str(config.get("openrouter_api_key_env", "OPENROUTER_API_KEY")),
        openrouter_model=str(config.get("openrouter_model", "openai/gpt-4o-mini")),
        openrouter_base_url=str(
            config.get("openrouter_base_url", "https://openrouter.ai/api/v1")
        ),
        openrouter_timeout_seconds=float(
            config.get("openrouter_timeout_seconds", 30)
        ),
        openrouter_max_retries=int(config.get("openrouter_max_retries", 2)),
        openrouter_mock_mode=_coerce_bool(config.get("openrouter_mock_mode", True)),
    )


def validate_hybrid_config(config: HybridConfig):
    if not 0 <= config.ai_participant_proportion <= 100:
        raise ValueError("ai_participant_proportion must be between 0 and 100.")
    if config.target_n_participants is not None and config.target_n_participants <= 0:
        raise ValueError("target_n_participants must be a positive integer when set.")
    if config.ai_scheduler_enabled and config.target_n_participants is None:
        raise ValueError("target_n_participants is required when the AI scheduler is enabled.")
    if config.ai_scheduler_max_running_bots < 1:
        raise ValueError("ai_scheduler_max_running_bots must be at least 1.")
    if config.openrouter_timeout_seconds <= 0:
        raise ValueError("openrouter_timeout_seconds must be positive.")
    if config.openrouter_max_retries < 0:
        raise ValueError("openrouter_max_retries must be non-negative.")
    if not config.openrouter_base_url:
        raise ValueError("openrouter_base_url must not be empty.")
    if not config.openrouter_model:
        raise ValueError("openrouter_model must not be empty.")
    if (
        config.ai_participant_proportion > 0
        and not config.openrouter_mock_mode
        and not os.environ.get(config.openrouter_api_key_env)
    ):
        raise ValueError(
            "OpenRouter API key is required when AI participants are enabled "
            "and openrouter_mock_mode is false."
        )


def build_color_stimulus(trial, participant) -> Dict[str, object]:
    group = getattr(getattr(participant, "module_state", None), "participant_group", None)
    if group is None:
        group = var_get(participant, "participant_group")

    active_color = COLORS[trial.active_index]
    starting_values = [int(value) for value in trial.initial_vector]
    return {
        "target": trial.context["target"],
        "participant_group": group,
        "starting_values": dict(zip(COLORS, starting_values)),
        "active_color": active_color,
        "active_index": int(trial.active_index),
        "min_value": 0,
        "max_value": 255,
    }


def render_human_prompt(stimulus: Dict[str, object]) -> Markup:
    return Markup(
        f"<h3 id='participant-group'>Participant group = {stimulus['participant_group']}</h3>"
        "<p>Adjust the slider to match the following word as well as possible: "
        f"<strong>{stimulus['target']}</strong></p>"
    )


def render_ai_prompt(stimulus: Dict[str, object]) -> str:
    return (
        "You are completing a color-matching trial from a PsyNet Gibbs sampling "
        "experiment. Match the human participant task as closely as possible.\n\n"
        f"Target word: {stimulus['target']}\n"
        f"Participant group: {stimulus['participant_group']}\n"
        f"Current RGB values: {json.dumps(stimulus['starting_values'], sort_keys=True)}\n"
        f"Adjust only the {stimulus['active_color']} channel.\n"
        f"Allowed value range: integer {stimulus['min_value']} to {stimulus['max_value']}.\n\n"
        'Respond with strict JSON only, using the schema {"value": 127}.'
    )


def parse_ai_slider_response(text: str) -> int:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError("AI response must be strict JSON.") from err

    if not isinstance(payload, dict) or set(payload) != {"value"}:
        raise ValueError('AI response must have exactly one key: "value".')

    value = payload["value"]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("AI response value must be an integer.")
    if not 0 <= value <= 255:
        raise ValueError("AI response value must be between 0 and 255.")
    return value


def mock_ai_slider_value(stimulus: Dict[str, object]) -> int:
    values = stimulus["starting_values"]
    assert isinstance(values, dict)
    target_offset = sum(ord(char) for char in str(stimulus["target"])) % 256
    fixed_mean = sum(int(values[color]) for color in COLORS) // len(COLORS)
    return int((fixed_mean + target_offset) % 256)


def call_openrouter_for_slider(stimulus: Dict[str, object], config: HybridConfig):
    prompt = render_ai_prompt(stimulus)
    metadata = {
        "controller": "ai",
        "prompt_template_version": AI_PROMPT_TEMPLATE_VERSION,
        "model": config.openrouter_model,
        "mock_mode": config.openrouter_mock_mode,
        "parser_status": "not_run",
        "retries": 0,
    }
    started_at = time.monotonic()

    if config.openrouter_mock_mode:
        metadata["parser_status"] = "mock"
        metadata["latency_seconds"] = round(time.monotonic() - started_at, 4)
        return mock_ai_slider_value(stimulus), metadata

    api_key = os.environ[config.openrouter_api_key_env]
    endpoint = f"{config.openrouter_base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": config.openrouter_model,
        "messages": [
            {
                "role": "system",
                "content": "Return only strict JSON for a color-slider response.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    last_error = None
    for attempt in range(config.openrouter_max_retries + 1):
        metadata["retries"] = attempt
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=config.openrouter_timeout_seconds,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            value = parse_ai_slider_response(content)
            metadata["parser_status"] = "ok"
            metadata["latency_seconds"] = round(time.monotonic() - started_at, 4)
            return value, metadata
        except Exception as err:  # noqa: BLE001 - convert provider/parsing failures.
            last_error = err

    metadata["parser_status"] = "error"
    metadata["latency_seconds"] = round(time.monotonic() - started_at, 4)
    raise ValueError(f"OpenRouter slider response failed: {last_error}") from last_error


def choose_ai_launch_count(state: HybridSchedulerState, target_proportion: float) -> int:
    if state.participant_target is None or target_proportion <= 0:
        return 0

    total = state.human_count + state.ai_count
    remaining_by_target = max(0, state.participant_target - total)
    if state.trial_capacity_remaining is not None:
        remaining_by_target = min(remaining_by_target, state.trial_capacity_remaining)
    if remaining_by_target == 0:
        return 0

    available_slots = max(0, state.ai_count + remaining_by_target - state.ai_count)
    available_running = max(0, state.running_ai_count)

    if total == 0:
        if target_proportion >= 100:
            return min(remaining_by_target, available_slots)
        return 0

    launch_count = 0
    while launch_count < remaining_by_target:
        projected_ai = state.ai_count + launch_count
        projected_total = total + launch_count
        if projected_total > 0 and (100 * projected_ai / projected_total) >= target_proportion:
            break
        launch_count += 1

    launch_count = min(launch_count, remaining_by_target, available_slots)
    if state.running_ai_count:
        launch_count = max(0, launch_count - available_running)
    return launch_count


def should_assign_ai_for_sequence(index: int, total: int, target_proportion: float) -> bool:
    if total <= 0 or target_proportion <= 0:
        return False
    if target_proportion >= 100:
        return index < total
    previous_target = math.floor(index * target_proportion / 100 + 0.5)
    current_target = math.floor((index + 1) * target_proportion / 100 + 0.5)
    return index < total and current_target > previous_target


class ColorSliderPage(ModularPage):
    def __init__(
        self,
        label: str,
        prompt: Union[str, Markup],
        selected_idx: int,
        starting_values: List[int],
        reverse_scale: bool,
        directional: bool,
        stimulus: Dict[str, object],
        bot_response=None,
        time_estimate=None,
        **kwargs,
    ):
        assert selected_idx >= 0 and selected_idx < len(COLORS)
        self.prompt = prompt
        self.selected_idx = selected_idx
        self.starting_values = starting_values
        self.stimulus = stimulus

        not_selected_idxs = list(range(len(COLORS)))
        not_selected_idxs.remove(selected_idx)
        not_selected_colors = [COLORS[i] for i in not_selected_idxs]
        not_selected_values = [starting_values[i] for i in not_selected_idxs]
        hidden_inputs = dict(zip(not_selected_colors, not_selected_values))
        kwargs["template_arg"] = {
            "hidden_inputs": hidden_inputs,
        }
        super().__init__(
            label,
            Prompt(prompt),
            control=SliderControl(
                start_value=starting_values[selected_idx],
                min_value=0,
                max_value=255,
                slider_id=COLORS[selected_idx],
                reverse_scale=reverse_scale,
                directional=directional,
                template_filename="color-slider.html",
                template_args={
                    "hidden_inputs": hidden_inputs,
                },
                continuous_updates=False,
                bot_response=bot_response or (lambda: random.randint(0, 255)),
            ),
            time_estimate=time_estimate,
        )

    def metadata(self, **kwargs):
        return {
            "prompt": self.prompt.metadata,
            "selected_idx": self.selected_idx,
            "starting_values": self.starting_values,
            "stimulus": self.stimulus,
        }


def color_slider_bot_response(experiment, bot, page):
    controller = var_get(bot, "controller", "human")
    if controller != "ai":
        return BotResponse(
            answer=random.randint(0, 255),
            metadata={"controller": controller, "profile": "simulated_human"},
        )

    config = read_hybrid_config()
    validate_hybrid_config(config)
    value, metadata = call_openrouter_for_slider(page.stimulus, config)
    bot.var.ai_profile = "mock_openrouter" if config.openrouter_mock_mode else "openrouter"
    return BotResponse(answer=value, metadata=metadata)


class CustomNetwork(GibbsNetwork):
    run_async_post_grow_network = True

    def async_post_grow_network(self):
        # This is a silly example of how we might define a function that runs every time
        # the network grows.
        try:
            self.var.growth_counter += 1
        except KeyError:
            self.var.growth_counter = 1


class CustomTrial(GibbsTrial):
    # If True, then the starting value for the free parameter is resampled
    # on each trial.
    run_async_post_trial = True
    resample_free_parameter = True
    time_estimate = 5

    def show_trial(self, experiment, participant):
        stimulus = build_color_stimulus(self, participant)
        prompt = render_human_prompt(stimulus)
        page = ColorSliderPage(
            "color_trial",
            prompt,
            starting_values=self.initial_vector,
            selected_idx=self.active_index,
            reverse_scale=self.reverse_scale,
            directional=False,
            stimulus=stimulus,
            bot_response=color_slider_bot_response,
            time_estimate=5,
        )
        return [
            page,
            # You can also include code blocks within a trial.
            # This one doesn't do anything useful, it's just there for demonstration purposes.
            CodeBlock(lambda participant: participant.var.set("test_variable", 123)),
        ]

    def async_post_trial(self):
        # You could put a time-consuming analysis here, perhaps one that generates a plot...
        time.sleep(1)
        self.var.async_post_trial_completed = True
        with tempfile.NamedTemporaryFile("w") as file:
            file.write(f"completed async_post_trial for trial {self.id}")
            file.flush()
            _asset = asset(
                file.name,
                local_key="async_post_trial",
                extension=".txt",
                parent=self,
            )
            _asset.deposit()


class CustomNode(GibbsNode):
    vector_length = 3

    def random_sample(self, i):
        return random.randint(0, 255)


class CustomTrialMaker(GibbsTrialMaker):
    give_end_feedback_passed = True
    performance_threshold = -1.0

    # If we set this to True, then the performance check will wait until all async_post_trial processes have finished
    end_performance_check_waits = False

    def prioritize_networks(self, networks, participant, experiment):
        for network in networks:
            network.alive_trials_at_degree = len(
                TrialNode.query.filter_by(network_id=network.id)
                .order_by(TrialNode.id)
                .all()[-1]
                .alive_trials
            )

        # Prioritize nodes with the most alive trials
        return list(reversed(sorted(networks, key=lambda n: n.alive_trials_at_degree)))

    def get_end_feedback_passed_page(self, score):
        score_to_display = "NA" if score is None else f"{(100 * score):.0f}"

        return InfoPage(
            Markup(
                f"Your consistency score was <strong>{score_to_display}&#37;</strong>."
            ),
            time_estimate=5,
        )

    def compute_performance_reward(self, score, passed):
        if score is None:
            return 0.0
        else:
            return max(0.0, score)

    def custom_network_filter(self, candidates, participant):
        # As an example, let's make the participant join networks
        # in order of increasing network ID.
        return sorted(candidates, key=lambda x: x.id)


start_nodes = [
    CustomNode(context={"target": target}, participant_group=participant_group)
    for target in TARGETS
    for participant_group in ["A", "B"]
]

trial_maker = CustomTrialMaker(
    id_="gibbs_demo",
    start_nodes=start_nodes,
    network_class=CustomNetwork,
    trial_class=CustomTrial,
    node_class=CustomNode,
    chain_type="across",  # can be "within" or "across"
    expected_trials_per_participant=4,
    max_trials_per_participant=4,
    max_nodes_per_chain=2,
    chains_per_participant=None,  # set to None if chain_type="across"
    chains_per_experiment=8,  # set to None if chain_type="within"
    trials_per_node=2,
    balance_across_chains=True,
    check_performance_at_end=True,
    check_performance_every_trial=False,
    propagate_failure=False,
    recruit_mode="n_trials",
    target_n_participants=None,
    n_repeat_trials=3,
    wait_for_networks=True,  # wait for asynchronous processes to complete before continuing to the next trial
    choose_participant_group=lambda participant: participant.var.participant_group,
)


###################
# This code is borrowed from the custom_table_simple demo.
# It is totally irrelevant for the Gibbs implementation.
# We just include it so we can test the export functionality
# in the regression tests.
@register_table
class Coin(SQLBase, SQLMixin):
    __tablename__ = "coin"

    participant = relationship(Participant, backref="all_coins")
    participant_id = Column(Integer, ForeignKey("participant.id"), index=True)

    def __init__(self, participant):
        self.participant = participant
        self.participant_id = participant.id


def collect_coin():
    return CodeBlock(_collect_coin)


def _collect_coin(participant):
    coin = Coin(participant)
    coin.var.test = "123"
    db.session.add(coin)


def mark_controller_and_schedule_ai(participant):
    if isinstance(participant, Bot):
        if var_get(participant, "controller") is None:
            participant.var.controller = "human"
        if participant.var.controller == "ai":
            participant.var.ai_profile = var_get(participant, "ai_profile", "mock_openrouter")
    else:
        participant.var.controller = "human"
        participant.var.ai_profile = None

    psynet.experiment.get_experiment().check_and_launch_ai_participants(
        trigger="participant_started"
    )


def schedule_ai_checkpoint(participant):
    psynet.experiment.get_experiment().check_and_launch_ai_participants(
        trigger="participant_checkpoint"
    )


class Exp(psynet.experiment.Experiment):
    label = "Hybrid Gibbs demo"

    @classmethod
    def extra_parameters(cls):
        super().extra_parameters()
        config = get_config()
        config.register("ai_participant_proportion", float)
        config.register("target_n_participants", int)
        config.register("ai_scheduler_enabled", bool)
        config.register("ai_scheduler_max_running_bots", int)
        config.register("openrouter_api_key_env", str)
        config.register("openrouter_model", str)
        config.register("openrouter_base_url", str)
        config.register("openrouter_timeout_seconds", float)
        config.register("openrouter_max_retries", int)
        config.register("openrouter_mock_mode", bool)

    timeline = Timeline(
        ModularPage(
            "choose_network",
            Prompt("What participant group would you like to join?"),
            control=PushButtonControl(["A", "B"], arrange_vertically=False),
            time_estimate=5,
            save_answer="participant_group",
            bot_response=lambda bot: ["A", "B"][bot.id % 2],
        ),
        CodeBlock(mark_controller_and_schedule_ai),
        trial_maker,
        collect_coin(),
        CodeBlock(schedule_ai_checkpoint),
        ExperimentFeedback(),
    )

    test_n_bots = 8

    def on_launch(self):
        config = read_hybrid_config()
        validate_hybrid_config(config)
        super().on_launch()
        self.check_and_launch_ai_participants(trigger="launch")

    def initialize_bot(self, bot):
        super().initialize_bot(bot)
        config = read_hybrid_config()
        validate_hybrid_config(config)

        target = config.target_n_participants or self.test_n_bots
        bot_index = max(0, Bot.query.count() - 1)
        should_be_ai = should_assign_ai_for_sequence(
            bot_index, target, config.ai_participant_proportion
        )
        bot.var.controller = "ai" if should_be_ai else "human"
        bot.var.ai_profile = (
            "mock_openrouter" if config.openrouter_mock_mode and should_be_ai else None
        )

    @classmethod
    def run_bot(cls, bot=None, render_pages=True, time_factor=0.0):
        super().run_bot(bot=bot, render_pages=render_pages, time_factor=time_factor)

    @classmethod
    def get_hybrid_scheduler_state(cls, include_unmarked=True) -> HybridSchedulerState:
        config = read_hybrid_config()
        participants = Participant.query.all()
        human_count = 0
        ai_count = 0
        running_ai_count = 0

        for participant in participants:
            controller = var_get(participant, "controller")
            if controller is None and include_unmarked and not isinstance(participant, Bot):
                controller = "human"
            if controller == "human":
                human_count += 1
            elif controller == "ai":
                ai_count += 1
                if participant.status == "working":
                    running_ai_count += 1

        if config.target_n_participants is None:
            trial_capacity_remaining = None
        else:
            trial_capacity_remaining = max(
                0, config.target_n_participants - human_count - ai_count
            )

        return HybridSchedulerState(
            human_count=human_count,
            ai_count=ai_count,
            running_ai_count=running_ai_count,
            participant_target=config.target_n_participants,
            trial_capacity_remaining=trial_capacity_remaining,
        )

    def check_and_launch_ai_participants(self, trigger="manual"):
        config = read_hybrid_config()
        validate_hybrid_config(config)
        if not config.ai_scheduler_enabled:
            return {"trigger": trigger, "launched": 0, "reason": "scheduler_disabled"}

        state = self.get_hybrid_scheduler_state()
        launch_count = choose_ai_launch_count(
            state, config.ai_participant_proportion
        )
        launch_count = min(
            launch_count,
            max(0, config.ai_scheduler_max_running_bots - state.running_ai_count),
        )

        for _ in range(launch_count):
            thread = threading.Thread(
                target=self.run_bot,
                kwargs={"render_pages": True, "time_factor": 0.0},
                daemon=True,
            )
            thread.start()

        self.var.set(
            "last_ai_scheduler_report",
            {
                "trigger": trigger,
                "state": state.__dict__,
                "target_proportion": config.ai_participant_proportion,
                "launched": launch_count,
            },
        )
        return self.var.last_ai_scheduler_report

    def test_check_bots(self, bots: List[Bot]):
        time.sleep(2.0)

        assert len([b for b in bots if b.var.participant_group == "A"]) == 4
        assert len([b for b in bots if b.var.participant_group == "B"]) == 4
        assert all(b.var.controller in {"human", "ai"} for b in bots)
        config = read_hybrid_config()
        target = min(len(bots), config.target_n_participants or len(bots))
        expected_ai = round(target * config.ai_participant_proportion / 100)
        controllers = [b.var.controller for b in bots]
        actual_ai = len([controller for controller in controllers if controller == "ai"])
        assert abs(actual_ai - expected_ai) <= 1, (
            f"Expected approximately {expected_ai} AI bots, saw {actual_ai}: "
            f"{controllers}"
        )

        for b in bots:
            assert len(b.alive_trials) == 7  # 4 normal trials + 3 repeat trials
            assert all([t.finalized for t in b.alive_trials])

        processes = AsyncProcess.query.all()
        assert all([not p.failed for p in processes])

        super().test_check_bots(bots)
