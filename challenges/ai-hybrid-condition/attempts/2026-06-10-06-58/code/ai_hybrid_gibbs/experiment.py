import hashlib
import os
import random
import tempfile
import time
from typing import List, Union

from dallinger import db
from markupsafe import Markup
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
AI_POLICY_NAME = "local_target_color_policy_v1"
AI_SHARE_ENV_VAR = "AI_SHARE"
GOLDEN_RATIO_CONJUGATE = 0.6180339887498949


def parse_ai_share(value=None):
    if value is None:
        value = os.getenv(AI_SHARE_ENV_VAR, "0.5")
    try:
        ai_share = float(value)
    except ValueError as exc:
        raise ValueError(f"{AI_SHARE_ENV_VAR} must be a number from 0 to 1.") from exc
    if not 0 <= ai_share <= 1:
        raise ValueError(f"{AI_SHARE_ENV_VAR} must be between 0 and 1.")
    return ai_share


AI_SHARE = parse_ai_share()


def choose_response_source(participant_id, ai_share=AI_SHARE):
    if ai_share <= 0:
        return "human"
    if ai_share >= 1:
        return "ai"
    low_discrepancy_position = (participant_id * GOLDEN_RATIO_CONJUGATE) % 1
    return "ai" if low_discrepancy_position < ai_share else "human"


def assign_response_source(participant):
    response_source = choose_response_source(participant.id)
    participant.var.response_source = response_source
    participant.var.ai_share = AI_SHARE
    if response_source == "ai":
        participant.var.ai_policy = AI_POLICY_NAME
    else:
        participant.var.ai_policy = None


def get_response_source(participant):
    return participant.var.get("response_source", default="human")


class LocalColorAIPolicy:
    target_palette = {
        "tree": {"red": 65, "green": 160, "blue": 75},
        "rock": {"red": 128, "green": 126, "blue": 120},
        "carrot": {"red": 230, "green": 112, "blue": 35},
        "banana": {"red": 238, "green": 216, "blue": 47},
    }

    def choose(self, target, color, starting_values, participant_id, trial_id):
        palette_value = self.target_palette[target][color]
        digest = hashlib.sha256(
            f"{target}:{color}:{participant_id}:{trial_id}".encode("utf-8")
        ).hexdigest()
        jitter = int(digest[:2], 16) % 17 - 8
        anchor = int(starting_values[COLORS.index(color)])
        response = round(0.8 * palette_value + 0.2 * anchor + jitter)
        return max(0, min(255, response))


AI_POLICY = LocalColorAIPolicy()


def color_slider_bot_response(bot, page):
    response_source = get_response_source(bot)
    if response_source == "ai":
        answer = AI_POLICY.choose(
            target=page.target,
            color=COLORS[page.selected_idx],
            starting_values=page.starting_values,
            participant_id=bot.id,
            trial_id=bot.current_trial.id,
        )
        metadata = {
            "response_source": "ai",
            "ai_share": AI_SHARE,
            "ai_policy": AI_POLICY_NAME,
        }
        return BotResponse(answer=answer, metadata=metadata)

    return BotResponse(
        answer=random.randint(0, 255),
        metadata={"response_source": "human", "ai_share": AI_SHARE},
    )


class ColorSliderPage(ModularPage):
    def __init__(
        self,
        label: str,
        prompt: Union[str, Markup],
        target: str,
        selected_idx: int,
        starting_values: List[int],
        reverse_scale: bool,
        directional: bool,
        time_estimate=None,
        **kwargs,
    ):
        assert selected_idx >= 0 and selected_idx < len(COLORS)
        self.prompt = prompt
        self.target = target
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
                bot_response=color_slider_bot_response,
            ),
            time_estimate=time_estimate,
        )

    def metadata(self, **kwargs):
        return {
            "prompt": self.prompt.metadata,
            "target": self.target,
            "selected_idx": self.selected_idx,
            "starting_values": self.starting_values,
        }


class CustomNetwork(GibbsNetwork):
    run_async_post_grow_network = True

    def async_post_grow_network(self):
        try:
            self.var.growth_counter += 1
        except KeyError:
            self.var.growth_counter = 1


class CustomTrial(GibbsTrial):
    run_async_post_trial = True
    resample_free_parameter = True
    time_estimate = 5

    def show_trial(self, experiment, participant):
        target = self.context["target"]
        prompt = Markup(
            f"<h3 id='participant-group'>Participant group = {participant.module_state.participant_group}</h3>"
            "<p>Adjust the slider to match the following word as well as possible: "
            f"<strong>{target}</strong></p>"
        )
        page = ColorSliderPage(
            "color_trial",
            prompt,
            target=target,
            starting_values=self.initial_vector,
            selected_idx=self.active_index,
            reverse_scale=self.reverse_scale,
            directional=False,
            time_estimate=5,
        )
        return [
            page,
            CodeBlock(lambda participant: participant.var.set("test_variable", 123)),
        ]

    def async_post_trial(self):
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
    end_performance_check_waits = False

    def finalize_trial(self, answer, trial, experiment, participant):
        response_source = get_response_source(participant)
        trial.var.response_source = response_source
        trial.var.ai_share = participant.var.get("ai_share", default=AI_SHARE)
        trial.var.ai_policy = (
            participant.var.get("ai_policy", default=None)
            if response_source == "ai"
            else None
        )
        super().finalize_trial(answer, trial, experiment, participant)

    def prioritize_networks(self, networks, participant, experiment):
        for network in networks:
            network.alive_trials_at_degree = len(
                TrialNode.query.filter_by(network_id=network.id)
                .order_by(TrialNode.id)
                .all()[-1]
                .alive_trials
            )

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
    chain_type="across",
    expected_trials_per_participant=4,
    max_trials_per_participant=4,
    max_nodes_per_chain=2,
    chains_per_participant=None,
    chains_per_experiment=8,
    trials_per_node=2,
    balance_across_chains=True,
    check_performance_at_end=True,
    check_performance_every_trial=False,
    propagate_failure=False,
    recruit_mode="n_trials",
    target_n_participants=None,
    n_repeat_trials=3,
    wait_for_networks=True,
    choose_participant_group=lambda participant: participant.var.participant_group,
)


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


def choose_network_page():
    return ModularPage(
        "choose_network",
        Prompt("What participant group would you like to join?"),
        control=PushButtonControl(["A", "B"], arrange_vertically=False),
        time_estimate=5,
        save_answer="participant_group",
        bot_response=lambda bot: ["A", "B"][bot.id % 2],
    )


def expected_source_counts(participant_ids, ai_share=AI_SHARE):
    counts = {"human": 0, "ai": 0}
    for participant_id in participant_ids:
        counts[choose_response_source(participant_id, ai_share)] += 1
    return counts


class Exp(psynet.experiment.Experiment):
    label = "AI-hybrid Gibbs demo"

    timeline = Timeline(
        choose_network_page(),
        CodeBlock(assign_response_source),
        trial_maker,
        collect_coin(),
        ExperimentFeedback(),
    )

    test_n_bots = 6

    def test_check_bots(self, bots: List[Bot]):
        time.sleep(2.0)

        assert len([b for b in bots if b.var.participant_group == "A"]) == 3
        assert len([b for b in bots if b.var.participant_group == "B"]) == 3

        observed_counts = {"human": 0, "ai": 0}
        for b in bots:
            response_source = b.var.response_source
            observed_counts[response_source] += 1
            assert b.var.ai_share == AI_SHARE
            assert len(b.alive_trials) == 7
            assert all([t.finalized for t in b.alive_trials])
            assert all([t.var.response_source == response_source for t in b.alive_trials])
            assert all([t.var.ai_share == AI_SHARE for t in b.alive_trials])
            if response_source == "ai":
                assert b.var.ai_policy == AI_POLICY_NAME
                assert all([t.var.ai_policy == AI_POLICY_NAME for t in b.alive_trials])

        assert observed_counts == expected_source_counts([b.id for b in bots])

        processes = AsyncProcess.query.all()
        assert all([not p.failed for p in processes])

        super().test_check_bots(bots)
