import json
import os
import random
import re
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from dallinger import db
from markupsafe import Markup
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

import psynet.experiment
from psynet.asset import asset
from psynet.bot import Bot, BotDriver, BotResponse
from psynet.data import SQLBase, SQLMixin, register_table
from psynet.db import transaction, with_transaction
from psynet.demography.general import ExperimentFeedback
from psynet.experiment import scheduled_task
from psynet.modular_page import ModularPage, Prompt, PushButtonControl, SliderControl
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.process import AsyncProcess, WorkerAsyncProcess
from psynet.timeline import CodeBlock, Timeline
from psynet.trial.gibbs import GibbsNetwork, GibbsNode, GibbsTrial, GibbsTrialMaker
from psynet.trial.main import TrialNode
from psynet.utils import get_config, get_logger

logger = get_logger()

TARGETS = ["tree", "rock", "carrot", "banana"]
COLORS = ["red", "green", "blue"]
SLIDER_MIN = 0
SLIDER_MAX = 255
HUMAN_TASK_INSTRUCTION = "Adjust the slider to match the following word as well as possible"


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _get_config_value(key: str, default: Any) -> Any:
    env_key = f"PSYNET_{key.upper()}"
    if env_key in os.environ:
        return os.environ[env_key]

    try:
        value = get_config().get(key, default=default)
    except TypeError:
        try:
            value = get_config().get(key)
        except Exception:
            value = default
    except Exception:
        value = default

    return default if value in (None, "") else value


@dataclass(frozen=True)
class HybridSettings:
    ai_proportion: int = 0
    target_n_participants: int = 6
    trial_capacity_participants: int = 6
    openrouter_api_key_env: str = "OPENROUTER_API_KEY"
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_timeout: float = 30.0
    openrouter_max_retries: int = 2
    openrouter_mock: bool = True
    ai_bot_time_factor: float = 0.0

    @classmethod
    def from_config(cls):
        settings = cls(
            ai_proportion=int(_get_config_value("hybrid_ai_proportion", cls.ai_proportion)),
            target_n_participants=int(
                _get_config_value("hybrid_target_n_participants", cls.target_n_participants)
            ),
            trial_capacity_participants=int(
                _get_config_value(
                    "hybrid_trial_capacity_participants",
                    cls.trial_capacity_participants,
                )
            ),
            openrouter_api_key_env=str(
                _get_config_value(
                    "hybrid_openrouter_api_key_env",
                    cls.openrouter_api_key_env,
                )
            ),
            openrouter_model=str(
                _get_config_value("hybrid_openrouter_model", cls.openrouter_model)
            ),
            openrouter_base_url=str(
                _get_config_value("hybrid_openrouter_base_url", cls.openrouter_base_url)
            ),
            openrouter_timeout=float(
                _get_config_value("hybrid_openrouter_timeout", cls.openrouter_timeout)
            ),
            openrouter_max_retries=int(
                _get_config_value(
                    "hybrid_openrouter_max_retries",
                    cls.openrouter_max_retries,
                )
            ),
            openrouter_mock=_coerce_bool(
                _get_config_value("hybrid_openrouter_mock", cls.openrouter_mock)
            ),
            ai_bot_time_factor=float(
                _get_config_value("hybrid_ai_bot_time_factor", cls.ai_bot_time_factor)
            ),
        )
        settings.validate()
        return settings

    @property
    def ai_fraction(self) -> float:
        return self.ai_proportion / 100.0

    def validate(self):
        if not 0 <= self.ai_proportion <= 100:
            raise ValueError("hybrid_ai_proportion must be between 0 and 100.")
        if self.target_n_participants < 1:
            raise ValueError("hybrid_target_n_participants must be at least 1.")
        if self.trial_capacity_participants < 1:
            raise ValueError("hybrid_trial_capacity_participants must be at least 1.")
        if not self.openrouter_api_key_env:
            raise ValueError("hybrid_openrouter_api_key_env must name an environment variable.")
        if not self.openrouter_model:
            raise ValueError("hybrid_openrouter_model must not be empty.")
        if not self.openrouter_base_url.startswith(("http://", "https://")):
            raise ValueError("hybrid_openrouter_base_url must be an HTTP(S) URL.")
        if self.openrouter_timeout <= 0:
            raise ValueError("hybrid_openrouter_timeout must be positive.")
        if self.openrouter_max_retries < 0:
            raise ValueError("hybrid_openrouter_max_retries must not be negative.")


def build_color_stimulus(target: str, selected_idx: int, starting_values: List[int]) -> Dict[str, Any]:
    values = {color: int(starting_values[i]) for i, color in enumerate(COLORS)}
    return {
        "target": target,
        "active_color": COLORS[selected_idx],
        "current_rgb": values,
        "scale_min": SLIDER_MIN,
        "scale_max": SLIDER_MAX,
    }


def build_human_prompt(stimulus: Dict[str, Any], participant_group: str) -> Markup:
    return Markup(
        f"<h3 id='participant-group'>Participant group = {participant_group}</h3>"
        f"<p>{HUMAN_TASK_INSTRUCTION}: "
        f"<strong>{stimulus['target']}</strong></p>"
    )


def build_ai_prompt(stimulus: Dict[str, Any], participant_group: str) -> str:
    return (
        "You are completing the same PsyNet Gibbs-sampling color task as a human participant.\n"
        f"Participant group: {participant_group}\n"
        f"Instruction: {HUMAN_TASK_INSTRUCTION}: {stimulus['target']}.\n"
        "The displayed color patch is defined by this RGB value: "
        f"{json.dumps(stimulus['current_rgb'], sort_keys=True)}.\n"
        f"Only the {stimulus['active_color']} channel is adjustable on this page. "
        f"Choose an integer from {stimulus['scale_min']} to {stimulus['scale_max']}.\n"
        'Reply with JSON only, using exactly this schema: {"answer": <integer>}.'
    )


def parse_ai_slider_answer(text: str) -> int:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.fullmatch(r"\s*(\d{1,3})\s*", text)
        if not match:
            raise ValueError("AI response was not valid JSON or a bare integer.")
        answer = int(match.group(1))
    else:
        if not isinstance(parsed, dict) or set(parsed) != {"answer"}:
            raise ValueError('AI response must be a JSON object with only an "answer" key.')
        answer = int(parsed["answer"])

    if not SLIDER_MIN <= answer <= SLIDER_MAX:
        raise ValueError("AI answer must be between 0 and 255.")
    return answer


def mock_openrouter_response(stimulus: Dict[str, Any]) -> str:
    color = stimulus["active_color"]
    current = stimulus["current_rgb"][color]
    target_offset = sum(ord(char) for char in stimulus["target"]) % 61 - 30
    answer = max(SLIDER_MIN, min(SLIDER_MAX, current + target_offset))
    return json.dumps({"answer": answer})


def call_openrouter(prompt: str, settings: HybridSettings) -> str:
    api_key = os.environ.get(settings.openrouter_api_key_env)
    if not api_key:
        raise RuntimeError(
            f"Set {settings.openrouter_api_key_env} or enable hybrid_openrouter_mock."
        )

    payload = {
        "model": settings.openrouter_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    url = f"{settings.openrouter_base_url.rstrip('/')}/chat/completions"

    for attempt in range(settings.openrouter_max_retries + 1):
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/pmcharrison/PsyNetSkills",
                "X-Title": "PsyNetSkills Gibbs hybrid participant attempt",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(  # nosec: challenge-specified OpenRouter URL
                request,
                timeout=settings.openrouter_timeout,
            ) as response:
                data = json.loads(response.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt >= settings.openrouter_max_retries:
                raise
            time.sleep(0.5 * (2**attempt))

    raise RuntimeError("OpenRouter call failed unexpectedly.")


def build_bot_response(
    stimulus: Dict[str, Any],
    participant_group: str,
    is_ai_participant: bool,
    settings: Optional[HybridSettings] = None,
) -> BotResponse:
    settings = settings or HybridSettings.from_config()
    if is_ai_participant:
        prompt = build_ai_prompt(stimulus, participant_group)
        raw_model_response = (
            mock_openrouter_response(stimulus)
            if settings.openrouter_mock
            else call_openrouter(prompt, settings)
        )
        answer = parse_ai_slider_answer(raw_model_response)
        metadata = {
            "participant_type": "ai",
            "openrouter_model": settings.openrouter_model,
            "openrouter_mock": settings.openrouter_mock,
            "stimulus": stimulus,
        }
    else:
        answer = random.randint(SLIDER_MIN, SLIDER_MAX)
        metadata = {"participant_type": "human_simulation", "stimulus": stimulus}

    return BotResponse(answer=answer, metadata=metadata)


def plan_ai_launches(
    human_count: int,
    ai_count: int,
    settings: HybridSettings,
    remaining_trial_capacity: int,
) -> int:
    settings.validate()
    if settings.ai_proportion == 0:
        return 0

    total_count = human_count + ai_count
    remaining_target = settings.target_n_participants - total_count
    max_new_bots = max(0, min(remaining_target, remaining_trial_capacity))
    if max_new_bots == 0:
        return 0

    if settings.ai_proportion == 100:
        return 1

    if total_count == 0:
        return 0

    for launch_count in range(max_new_bots + 1):
        future_total = total_count + launch_count
        future_ai_fraction = (ai_count + launch_count) / future_total
        if future_ai_fraction >= settings.ai_fraction:
            return launch_count
    return max_new_bots


class ColorSliderPage(ModularPage):
    def __init__(
        self,
        label: str,
        prompt: Union[str, Markup],
        selected_idx: int,
        starting_values: List[int],
        reverse_scale: bool,
        directional: bool,
        bot_response,
        time_estimate=None,
        **kwargs,
    ):
        assert selected_idx >= 0 and selected_idx < len(COLORS)
        self.prompt = prompt
        self.selected_idx = selected_idx
        self.starting_values = starting_values

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
                bot_response=bot_response,
            ),
            time_estimate=time_estimate,
        )

    def metadata(self, **kwargs):
        return {
            "prompt": self.prompt.metadata,
            "selected_idx": self.selected_idx,
            "starting_values": self.starting_values,
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
        target = self.context["target"]
        participant_group = participant.module_state.participant_group
        stimulus = build_color_stimulus(
            target=target,
            selected_idx=self.active_index,
            starting_values=self.initial_vector,
        )
        prompt = build_human_prompt(stimulus, participant_group)
        page = ColorSliderPage(
            "color_trial",
            prompt,
            starting_values=self.initial_vector,
            selected_idx=self.active_index,
            reverse_scale=self.reverse_scale,
            directional=False,
            bot_response=lambda bot: build_bot_response(
                stimulus=stimulus,
                participant_group=participant_group,
                is_ai_participant=bot.var.get("is_ai_participant", default=False),
            ),
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
    label = "Gibbs hybrid AI participant demo"

    timeline = Timeline(
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

    @classmethod
    def run_bot(
        cls,
        bot: Optional[BotDriver] = None,
        render_pages: bool = True,
        time_factor: float = 0.0,
        is_ai_participant: bool = False,
    ):
        if bot is None:
            bot = BotDriver()

        with transaction():
            bot_participant = Bot.query.get(bot.id)
            bot_participant.var.is_ai_participant = is_ai_participant

        bot.take_experiment(render_pages, time_factor)

    @staticmethod
    def current_hybrid_counts():
        total_count = Participant.query.count()
        ai_count = Bot.query.count()
        return {
            "human_count": max(0, total_count - ai_count),
            "ai_count": ai_count,
            "total_count": total_count,
        }

    @staticmethod
    def remaining_participant_capacity(settings: HybridSettings, total_count: int) -> int:
        return max(
            0,
            min(settings.target_n_participants, settings.trial_capacity_participants)
            - total_count,
        )

    @scheduled_task("interval", seconds=5.0, max_instances=1)
    @staticmethod
    @with_transaction
    def launch_ai_participants():
        from psynet.experiment import get_experiment, is_experiment_launched

        if not is_experiment_launched():
            return

        settings = HybridSettings.from_config()
        counts = Exp.current_hybrid_counts()
        remaining_capacity = Exp.remaining_participant_capacity(
            settings,
            counts["total_count"],
        )
        n_to_launch = plan_ai_launches(
            human_count=counts["human_count"],
            ai_count=counts["ai_count"],
            settings=settings,
            remaining_trial_capacity=remaining_capacity,
        )
        if n_to_launch == 0:
            return

        experiment = get_experiment()
        for _ in range(n_to_launch):
            WorkerAsyncProcess(
                function=experiment.run_bot,
                arguments={
                    "time_factor": settings.ai_bot_time_factor,
                    "is_ai_participant": True,
                },
            )
        db.session.commit()

    def test_check_bots(self, bots: List[Bot]):
        time.sleep(2.0)

        assert len([b for b in bots if b.var.participant_group == "A"]) == 3
        assert len([b for b in bots if b.var.participant_group == "B"]) == 3
        assert all(not b.var.get("is_ai_participant", default=False) for b in bots)

        for b in bots:
            assert len(b.alive_trials) == 7  # 4 normal trials + 3 repeat trials
            assert all([t.finalized for t in b.alive_trials])

        processes = AsyncProcess.query.all()
        assert all([not p.failed for p in processes])

        super().test_check_bots(bots)
