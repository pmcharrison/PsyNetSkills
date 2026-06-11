import json
import math
import os
import random
import re
import tempfile
import time
import urllib.error
import urllib.request
from typing import Callable, Dict, List, Mapping, Optional, Union

from dallinger import db
from dallinger.config import get_config
from markupsafe import Markup
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

import psynet.experiment
from psynet.asset import asset
from psynet.bot import Bot, BotDriver, BotResponse
from psynet.data import SQLBase, SQLMixin, register_table
from psynet.demography.general import ExperimentFeedback
from psynet.modular_page import ModularPage, Prompt, PushButtonControl, SliderControl
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.process import AsyncProcess, WorkerAsyncProcess
from psynet.timeline import CodeBlock, Timeline
from psynet.trial.gibbs import GibbsNetwork, GibbsNode, GibbsTrial, GibbsTrialMaker
from psynet.trial.main import TrialNode
from psynet.utils import get_logger

logger = get_logger()

TARGETS = ["tree", "rock", "carrot", "banana"]
COLORS = ["red", "green", "blue"]

HYBRID_CONFIG_DEFAULTS = {
    "ai_participant_proportion": 0.0,
    "ai_total_participant_target": 6,
    "openrouter_api_key_env_var": "OPENROUTER_API_KEY",
    "openrouter_model": "openai/gpt-4o-mini",
    "openrouter_base_url": "https://openrouter.ai/api/v1/chat/completions",
    "openrouter_timeout_seconds": 20.0,
    "openrouter_max_retries": 1,
    "openrouter_mock_mode": True,
}


def _read_config_value(config, key, default):
    if config is None:
        config = get_config()
    if isinstance(config, Mapping):
        return config.get(key, default)
    return config.get(key, default=default)


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value = value.strip().lower()
        if value in {"true", "1", "yes", "y"}:
            return True
        if value in {"false", "0", "no", "n"}:
            return False
    raise ValueError(f"Cannot interpret {value!r} as a boolean.")


def get_hybrid_config(config=None) -> Dict[str, object]:
    settings = {
        key: _read_config_value(config, key, default)
        for key, default in HYBRID_CONFIG_DEFAULTS.items()
    }
    settings["ai_participant_proportion"] = float(
        settings["ai_participant_proportion"]
    )
    settings["ai_total_participant_target"] = int(
        settings["ai_total_participant_target"]
    )
    settings["openrouter_timeout_seconds"] = float(
        settings["openrouter_timeout_seconds"]
    )
    settings["openrouter_max_retries"] = int(settings["openrouter_max_retries"])
    settings["openrouter_mock_mode"] = _as_bool(settings["openrouter_mock_mode"])
    validate_hybrid_config(settings)
    return settings


def validate_hybrid_config(settings: Mapping[str, object]):
    proportion = settings["ai_participant_proportion"]
    if not 0 <= proportion <= 100:
        raise ValueError("ai_participant_proportion must be between 0 and 100.")
    if settings["ai_total_participant_target"] < 0:
        raise ValueError("ai_total_participant_target must be non-negative.")
    if not str(settings["openrouter_api_key_env_var"]).strip():
        raise ValueError("openrouter_api_key_env_var must name an environment variable.")
    if not str(settings["openrouter_model"]).strip():
        raise ValueError("openrouter_model must be non-empty.")
    if not str(settings["openrouter_base_url"]).startswith(("http://", "https://")):
        raise ValueError("openrouter_base_url must be an HTTP(S) URL.")
    if settings["openrouter_timeout_seconds"] <= 0:
        raise ValueError("openrouter_timeout_seconds must be positive.")
    if settings["openrouter_max_retries"] < 0:
        raise ValueError("openrouter_max_retries must be non-negative.")
    if not settings["openrouter_mock_mode"] and not os.environ.get(
        str(settings["openrouter_api_key_env_var"])
    ):
        raise ValueError(
            "OpenRouter live mode requires the configured API key environment variable."
        )


def plan_ai_launches(
    *,
    human_count: int,
    ai_count: int,
    ai_running: int,
    total_participant_target: int,
    ai_participant_proportion: float,
) -> int:
    if min(human_count, ai_count, ai_running, total_participant_target) < 0:
        raise ValueError("Participant counts must be non-negative.")
    if not 0 <= ai_participant_proportion <= 100:
        raise ValueError("ai_participant_proportion must be between 0 and 100.")

    current_ai = ai_count + ai_running
    current_total = human_count + current_ai
    remaining_capacity = total_participant_target - current_total
    if remaining_capacity <= 0 or ai_participant_proportion == 0:
        return 0
    if ai_participant_proportion == 100:
        return remaining_capacity

    desired_ai_for_current_humans = math.ceil(
        human_count * ai_participant_proportion / (100 - ai_participant_proportion)
    )
    needed = desired_ai_for_current_humans - current_ai
    return max(0, min(needed, remaining_capacity))


def build_color_stimulus(
    *,
    target: str,
    participant_group: str,
    active_index: int,
    starting_values: List[int],
) -> Dict[str, object]:
    if not 0 <= active_index < len(COLORS):
        raise ValueError("active_index must select one of the RGB channels.")
    if len(starting_values) != len(COLORS):
        raise ValueError("starting_values must contain red, green, and blue values.")
    rgb = {color: int(value) for color, value in zip(COLORS, starting_values)}
    for value in rgb.values():
        if not 0 <= value <= 255:
            raise ValueError("RGB values must be between 0 and 255.")
    return {
        "target": target,
        "participant_group": participant_group,
        "active_color": COLORS[active_index],
        "active_index": active_index,
        "rgb": rgb,
    }


def build_human_prompt_html(stimulus: Mapping[str, object]) -> str:
    return (
        f"<h3 id='participant-group'>Participant group = "
        f"{stimulus['participant_group']}</h3>"
        "<p>Adjust the slider to match the following word as well as possible: "
        f"<strong>{stimulus['target']}</strong></p>"
    )


def format_ai_prompt(stimulus: Mapping[str, object]) -> str:
    rgb = stimulus["rgb"]
    return (
        "You are completing the same color-slider task as a human participant.\n"
        f"Participant group = {stimulus['participant_group']}.\n"
        "Adjust the slider to match the following word as well as possible: "
        f"{stimulus['target']}.\n"
        "The displayed color square is represented by these RGB values: "
        f"red={rgb['red']}, green={rgb['green']}, blue={rgb['blue']}.\n"
        f"You may adjust only the {stimulus['active_color']} channel.\n"
        "Return exactly one JSON object in this format: {\"value\": 0}.\n"
        "The value must be an integer from 0 to 255."
    )


def parse_ai_slider_response(content: str) -> int:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        matches = re.findall(r"-?\d+", content)
        if len(matches) != 1:
            raise ValueError("AI response must contain exactly one slider value.")
        value = int(matches[0])
    else:
        if not isinstance(parsed, Mapping) or set(parsed) != {"value"}:
            raise ValueError("AI response JSON must contain only a 'value' field.")
        value = int(parsed["value"])
    if not 0 <= value <= 255:
        raise ValueError("AI slider value must be between 0 and 255.")
    return value


def mock_openrouter_content(stimulus: Mapping[str, object]) -> str:
    rgb = stimulus["rgb"]
    value = (
        sum(ord(char) for char in str(stimulus["target"]))
        + rgb[str(stimulus["active_color"])]
        + 31 * int(stimulus["active_index"])
    ) % 256
    return json.dumps({"value": value})


def request_openrouter_content(
    prompt: str,
    settings: Mapping[str, object],
    request_fn: Optional[Callable] = None,
) -> str:
    payload = json.dumps(
        {
            "model": settings["openrouter_model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 20,
        }
    ).encode("utf-8")
    api_key = os.environ[str(settings["openrouter_api_key_env_var"])]
    request = urllib.request.Request(
        str(settings["openrouter_base_url"]),
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    last_error = None
    for _ in range(int(settings["openrouter_max_retries"]) + 1):
        try:
            if request_fn is None:
                with urllib.request.urlopen(
                    request,
                    timeout=float(settings["openrouter_timeout_seconds"]),
                ) as response:
                    response_payload = response.read().decode("utf-8")
            else:
                response_payload = request_fn(
                    request,
                    timeout=float(settings["openrouter_timeout_seconds"]),
                )
            if isinstance(response_payload, Mapping):
                data = response_payload
            else:
                data = json.loads(response_payload)
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, urllib.error.URLError) as error:
            last_error = error
    raise RuntimeError(f"OpenRouter request failed: {last_error}")


def bot_response(
    stimulus: Mapping[str, object],
    config=None,
    request_fn: Optional[Callable] = None,
) -> BotResponse:
    settings = get_hybrid_config(config)
    prompt = format_ai_prompt(stimulus)
    if settings["openrouter_mock_mode"]:
        content = mock_openrouter_content(stimulus)
    else:
        content = request_openrouter_content(prompt, settings, request_fn)
    value = parse_ai_slider_response(content)
    return BotResponse(
        answer=value,
        metadata={
            "participant_role": "ai",
            "ai_prompt": prompt,
            "ai_stimulus": dict(stimulus),
            "openrouter_model": settings["openrouter_model"],
            "openrouter_mock_mode": settings["openrouter_mock_mode"],
        },
    )


def ensure_participant_role(participant):
    if not participant.var.has("participant_role"):
        participant.var.set("participant_role", "human")


def is_ai_participant(participant) -> bool:
    return participant.var.get("participant_role", default="human") == "ai"


def mark_participant_role(participant_id: int, role: str):
    participant = Participant.query.get(participant_id)
    participant.var.set("participant_role", role)
    db.session.commit()


class ColorSliderPage(ModularPage):
    def __init__(
        self,
        label: str,
        prompt: Union[str, Markup],
        selected_idx: int,
        starting_values: List[int],
        reverse_scale: bool,
        directional: bool,
        stimulus: Mapping[str, object],
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
                bot_response=lambda bot: (
                    bot_response(self.stimulus) if is_ai_participant(bot) else random.randint(0, 255)
                ),
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
        stimulus = build_color_stimulus(
            target=self.context["target"],
            participant_group=participant.module_state.participant_group,
            active_index=self.active_index,
            starting_values=self.initial_vector,
        )
        prompt = Markup(build_human_prompt_html(stimulus))
        page = ColorSliderPage(
            "color_trial",
            prompt,
            starting_values=self.initial_vector,
            selected_idx=self.active_index,
            reverse_scale=self.reverse_scale,
            directional=False,
            stimulus=stimulus,
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


class Exp(psynet.experiment.Experiment):
    label = "Gibbs hybrid human-AI demo"
    config = HYBRID_CONFIG_DEFAULTS

    timeline = Timeline(
        CodeBlock(ensure_participant_role),
        ModularPage(
            "choose_network",
            Prompt("What participant group would you like to join?"),
            control=PushButtonControl(["A", "B"], arrange_vertically=False),
            time_estimate=5,
            save_answer="participant_group",
            bot_response=lambda bot: ["A", "B"][bot.id % 2],
        ),
        trial_maker,
        collect_coin(),
        ExperimentFeedback(),
    )

    test_n_bots = 6

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        get_hybrid_config()

    @classmethod
    def extra_parameters(cls):
        super().extra_parameters()
        config = get_config()
        config.register("ai_participant_proportion", float)
        config.register("ai_total_participant_target", int)
        config.register("openrouter_api_key_env_var", str)
        config.register("openrouter_model", str)
        config.register("openrouter_base_url", str)
        config.register("openrouter_timeout_seconds", float)
        config.register("openrouter_max_retries", int)
        config.register("openrouter_mock_mode", bool)

    @staticmethod
    def hybrid_participant_counts():
        counts = {"human": 0, "ai": 0, "ai_running": 0}
        for participant in Participant.query.all():
            if participant.failed:
                continue
            role = participant.var.get(
                "participant_role",
                default="ai" if isinstance(participant, Bot) else "human",
            )
            if role == "ai":
                counts["ai"] += 1
                if participant.status == "working":
                    counts["ai_running"] += 1
            else:
                counts["human"] += 1
        return counts

    def launch_scheduled_ai_bots(self, settings=None):
        settings = get_hybrid_config(settings)
        counts = self.hybrid_participant_counts()
        n_to_launch = plan_ai_launches(
            human_count=counts["human"],
            ai_count=counts["ai"],
            ai_running=counts["ai_running"],
            total_participant_target=settings["ai_total_participant_target"],
            ai_participant_proportion=settings["ai_participant_proportion"],
        )
        for _ in range(n_to_launch):
            WorkerAsyncProcess(function=self.run_ai_bot)
        if n_to_launch:
            self.var.set(
                "last_ai_scheduler_decision",
                {**counts, "launched": n_to_launch},
            )
            db.session.commit()
        return n_to_launch

    def recruit(self):
        settings = get_hybrid_config()
        if settings["ai_participant_proportion"] < 100:
            super().recruit()
        else:
            self.recruiter.close_recruitment()
        self.launch_scheduled_ai_bots(settings)

    @classmethod
    def run_bot(
        cls,
        bot: Optional[BotDriver] = None,
        render_pages: bool = True,
        time_factor: float = 0.0,
    ):
        if bot is None:
            bot = BotDriver()
        mark_participant_role(bot.id, "human")
        bot.take_experiment(render_pages, time_factor)

    @classmethod
    def run_ai_bot(
        cls,
        bot: Optional[BotDriver] = None,
        render_pages: bool = True,
        time_factor: float = 0.0,
    ):
        if bot is None:
            bot = BotDriver()
        mark_participant_role(bot.id, "ai")
        bot.take_experiment(render_pages, time_factor)

    def test_check_bots(self, bots: List[Bot]):
        time.sleep(2.0)

        assert all(b.var.get("participant_role", default="human") == "human" for b in bots)
        assert len([b for b in bots if b.var.participant_group == "A"]) == 3
        assert len([b for b in bots if b.var.participant_group == "B"]) == 3

        for b in bots:
            assert len(b.alive_trials) == 7  # 4 normal trials + 3 repeat trials
            assert all([t.finalized for t in b.alive_trials])

        processes = AsyncProcess.query.all()
        assert all([not p.failed for p in processes])

        super().test_check_bots(bots)
