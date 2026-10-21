import json
import os
import random
import re
import tempfile
import time
import urllib.error
import urllib.request
from typing import Dict, List, Union

from dallinger import db
from dallinger.config import get_config as dallinger_get_config
from markupsafe import Markup
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

import psynet.experiment
from psynet.asset import asset
from psynet.bot import Bot
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
OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"


def _validate_percentage(value):
    value = int(value)
    assert 0 <= value <= 100, "ai_participant_proportion must be between 0 and 100"


def _validate_nonnegative_int(value):
    assert int(value) >= 0


def _validate_positive_int(value):
    assert int(value) > 0


class HybridParticipantScheduler:
    @staticmethod
    def validate_proportion(proportion: int) -> int:
        proportion = int(proportion)
        if not 0 <= proportion <= 100:
            raise ValueError("AI participant proportion must be between 0 and 100.")
        return proportion

    @classmethod
    def target_ai_count(cls, total_participants: int, proportion: int) -> int:
        proportion = cls.validate_proportion(proportion)
        if total_participants < 0:
            raise ValueError("total_participants must be nonnegative.")
        return int((total_participants * proportion / 100) + 0.5)

    @classmethod
    def planned_assignments(cls, total_participants: int, proportion: int) -> List[str]:
        if total_participants < 0:
            raise ValueError("total_participants must be nonnegative.")
        assignments = []
        previous_ai_count = 0
        for i in range(1, total_participants + 1):
            next_ai_count = cls.target_ai_count(i, proportion)
            assignments.append("ai" if next_ai_count > previous_ai_count else "human")
            previous_ai_count = next_ai_count
        return assignments

    @classmethod
    def ai_bots_to_launch(
        cls, existing_ai_count: int, target_total_participants: int, proportion: int
    ) -> int:
        target_ai_count = cls.target_ai_count(target_total_participants, proportion)
        return max(0, target_ai_count - existing_ai_count)


def make_color_slider_stimulus(
    target: str,
    selected_idx: int,
    starting_values: List[int],
    participant_group: str,
) -> Dict:
    return {
        "target_word": target,
        "active_color": COLORS[selected_idx],
        "active_color_index": selected_idx,
        "starting_rgb": dict(zip(COLORS, starting_values)),
        "participant_group": participant_group,
        "slider_min": 0,
        "slider_max": 255,
    }


def build_ai_prompt(stimulus: Dict) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are completing the same color-word matching task as a human "
                "participant. Use only the stimulus provided. Return a JSON object "
                'with one integer field named "answer" between 0 and 255.'
            ),
        },
        {
            "role": "user",
            "content": (
                "A participant sees a color patch controlled by RGB sliders and is "
                "asked to adjust only the active slider to match the target word. "
                f"Stimulus: {json.dumps(stimulus, sort_keys=True)}"
            ),
        },
    ]


def parse_ai_slider_answer(text: str) -> int:
    try:
        data = json.loads(text)
        answer = data["answer"] if isinstance(data, dict) else data
    except (json.JSONDecodeError, KeyError, TypeError):
        match = re.search(r"-?\d+", text)
        if not match:
            raise ValueError(f"Could not parse an integer slider answer from: {text!r}")
        answer = match.group(0)

    answer = int(answer)
    if not 0 <= answer <= 255:
        raise ValueError(f"AI slider answer must be between 0 and 255, got {answer}.")
    return answer


def deterministic_slider_answer(stimulus: Dict) -> int:
    target = stimulus["target_word"]
    active_color = stimulus["active_color"]
    starting_rgb = stimulus["starting_rgb"]
    target_color_map = {
        "tree": {"red": 45, "green": 145, "blue": 50},
        "rock": {"red": 115, "green": 115, "blue": 115},
        "carrot": {"red": 235, "green": 120, "blue": 35},
        "banana": {"red": 240, "green": 220, "blue": 45},
    }
    return target_color_map.get(target, starting_rgb)[active_color]


class OpenRouterClient:
    def __init__(
        self, api_key: str, base_url: str, model: str, timeout: int, retries: int
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.retries = retries

    def complete(self, messages: List[Dict[str, str]]) -> str:
        body = json.dumps({"model": self.model, "messages": messages}).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        request = urllib.request.Request(
            self.base_url, data=body, headers=headers, method="POST"
        )
        last_error = None
        for _ in range(self.retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
            except (
                urllib.error.URLError,
                KeyError,
                IndexError,
                json.JSONDecodeError,
            ) as e:
                last_error = e
        raise RuntimeError(f"OpenRouter request failed: {last_error}")


def get_openrouter_client(experiment):
    config = dallinger_get_config()
    api_key_env = config.get("openrouter_api_key_env")
    api_key = os.environ.get(api_key_env)
    if not api_key:
        if config.get("openrouter_mock_when_missing_key"):
            return None
        raise RuntimeError(
            f"Missing OpenRouter API key environment variable: {api_key_env}"
        )
    return OpenRouterClient(
        api_key=api_key,
        base_url=config.get("openrouter_base_url"),
        model=config.get("openrouter_model"),
        timeout=config.get("openrouter_timeout_seconds"),
        retries=config.get("openrouter_max_retries"),
    )


def bot_response(experiment, bot, stimulus: Dict) -> int:
    client = get_openrouter_client(experiment)
    if client is None:
        bot.var.ai_response_source = "deterministic-local-fallback"
        return deterministic_slider_answer(stimulus)

    content = client.complete(build_ai_prompt(stimulus))
    answer = parse_ai_slider_answer(content)
    bot.var.ai_response_source = "openrouter"
    return answer


def initialize_hybrid_participant():
    return CodeBlock(_initialize_hybrid_participant)


def _initialize_hybrid_participant(participant, experiment):
    is_ai = isinstance(participant, Bot)
    participant.var.participant_controller = "ai" if is_ai else "human"
    participant.var.is_ai_participant = is_ai
    if not is_ai:
        experiment.launch_configured_ai_bots()


class ColorSliderPage(ModularPage):
    def __init__(
        self,
        label: str,
        prompt: Union[str, Markup],
        selected_idx: int,
        starting_values: List[int],
        reverse_scale: bool,
        directional: bool,
        stimulus: Dict,
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
                bot_response=lambda experiment, bot: bot_response(
                    experiment, bot, stimulus
                ),
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
        stimulus = make_color_slider_stimulus(
            target=target,
            selected_idx=self.active_index,
            starting_values=self.initial_vector,
            participant_group=participant_group,
        )
        prompt = Markup(
            f"<h3 id='participant-group'>Participant group = {participant_group}</h3>"
            "<p>Adjust the slider to match the following word as well as possible: "
            f"<strong>{target}</strong></p>"
        )
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
    label = "Gibbs demo"

    @classmethod
    def extra_parameters(cls):
        super().extra_parameters()
        config = dallinger_get_config()
        config.register(
            "ai_participant_proportion", int, validators=[_validate_percentage]
        )
        config.register(
            "ai_target_total_participants", int, validators=[_validate_nonnegative_int]
        )
        config.register("openrouter_api_key_env", str)
        config.register("openrouter_model", str)
        config.register("openrouter_base_url", str)
        config.register(
            "openrouter_timeout_seconds", int, validators=[_validate_positive_int]
        )
        config.register(
            "openrouter_max_retries", int, validators=[_validate_nonnegative_int]
        )
        config.register("openrouter_mock_when_missing_key", bool)

    @classmethod
    def config_defaults(cls):
        return {
            **super().config_defaults(),
            "ai_participant_proportion": 0,
            "ai_target_total_participants": 0,
            "openrouter_api_key_env": "OPENROUTER_API_KEY",
            "openrouter_model": "openai/gpt-4o-mini",
            "openrouter_base_url": OPENROUTER_CHAT_COMPLETIONS_URL,
            "openrouter_timeout_seconds": 20,
            "openrouter_max_retries": 2,
            "openrouter_mock_when_missing_key": True,
        }

    def launch_configured_ai_bots(self) -> int:
        config = dallinger_get_config()
        target_total = config.get("ai_target_total_participants")
        if target_total <= 0:
            return 0
        existing_ai_count = Bot.query.count()
        to_launch = HybridParticipantScheduler.ai_bots_to_launch(
            existing_ai_count=existing_ai_count,
            target_total_participants=target_total,
            proportion=config.get("ai_participant_proportion"),
        )
        for _ in range(to_launch):
            WorkerAsyncProcess(function=self.run_bot, label="hybrid_ai_bot")
        return to_launch

    timeline = Timeline(
        initialize_hybrid_participant(),
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

    def test_check_bots(self, bots: List[Bot]):
        time.sleep(2.0)

        assert len([b for b in bots if b.var.participant_group == "A"]) == 3
        assert len([b for b in bots if b.var.participant_group == "B"]) == 3

        for b in bots:
            assert len(b.alive_trials) == 7  # 4 normal trials + 3 repeat trials
            assert all([t.finalized for t in b.alive_trials])

        processes = AsyncProcess.query.all()
        assert all([not p.failed for p in processes])

        super().test_check_bots(bots)
