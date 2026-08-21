import json
import os
import random
import tempfile
import time
from collections import Counter, defaultdict
from typing import List, Union

from dallinger import db
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
from psynet.process import AsyncProcess
from psynet.timeline import CodeBlock, Timeline
from psynet.trial.gibbs import GibbsNetwork, GibbsNode, GibbsTrial, GibbsTrialMaker
from psynet.trial.main import TrialNode
from psynet.utils import get_logger

logger = get_logger()

TARGETS = ["tree", "rock", "carrot", "banana"]
COLORS = ["red", "green", "blue"]
BOT_PROFILE_COUNTS = {"random": 5, "normal_rgb": 5}
BOT_PROFILE_SEED = 20260615
NORMAL_RGB_SD = 30.0


def clip_rgb_channel(value):
    return int(max(0, min(255, round(value))))


def make_profile_roster(seed=BOT_PROFILE_SEED):
    roster = [
        profile
        for profile, count in BOT_PROFILE_COUNTS.items()
        for _ in range(count)
    ]
    random.Random(seed).shuffle(roster)
    return roster


def get_bot_profile(bot):
    try:
        return bot.var.bot_profile
    except KeyError:
        # Browser participants and ad-hoc bots outside the configured test roster
        # still need a valid response path.
        return "random"


def sample_bot_color_response(bot, selected_idx, starting_values):
    profile = get_bot_profile(bot)

    if profile == "random":
        return random.randint(0, 255)
    elif profile == "normal_rgb":
        center = starting_values[selected_idx]
        return clip_rgb_channel(random.normalvariate(center, NORMAL_RGB_SD))
    else:
        raise ValueError(f"Unknown bot profile: {profile}")


class ColorSliderPage(ModularPage):
    def __init__(
        self,
        label: str,
        prompt: Union[str, Markup],
        selected_idx: int,
        starting_values: List[int],
        reverse_scale: bool,
        directional: bool,
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
                bot_response=lambda bot: sample_bot_color_response(
                    bot=bot,
                    selected_idx=selected_idx,
                    starting_values=starting_values,
                ),
            ),
            time_estimate=time_estimate,
        )

    def metadata(self, **kwargs):
        return {
            "prompt": self.prompt.metadata,
            "selected_idx": self.selected_idx,
            "active_channel": COLORS[self.selected_idx],
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
        prompt = Markup(
            f"<h3 id='participant-group'>Participant group = {participant.module_state.participant_group}</h3>"
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
            time_estimate=5,
        )
        return [
            page,
            CodeBlock(lambda participant: self.record_profile_metadata(participant)),
            CodeBlock(lambda participant: participant.var.set("test_variable", 123)),
        ]

    def record_profile_metadata(self, participant):
        active_channel = COLORS[self.active_index]
        response = clip_rgb_channel(participant.answer)
        profile_metadata = {
            "bot_profile": get_bot_profile(participant),
            "participant_id": participant.id,
            "participant_group": participant.module_state.participant_group,
            "target": self.context["target"],
            "active_channel": active_channel,
            "active_index": self.active_index,
            "starting_values": self.initial_vector,
            "submitted_channel_response": response,
            "response_distance_from_start": abs(
                response - self.initial_vector[self.active_index]
            ),
        }
        self.var.profile_metadata = profile_metadata
        participant.var.last_color_response_metadata = profile_metadata

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
    bot_profile_seed = BOT_PROFILE_SEED
    bot_profile_roster = None
    bot_profile_cursor = 0

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

    test_n_bots = 10

    def initialize_bot(self, bot):
        super().initialize_bot(bot)
        bot.var.bot_profile = self.next_bot_profile()
        bot.var.bot_profile_seed = self.bot_profile_seed

    @classmethod
    def next_bot_profile(cls):
        if cls.bot_profile_roster is None:
            cls.bot_profile_roster = make_profile_roster(cls.bot_profile_seed)

        index = cls.bot_profile_cursor % len(cls.bot_profile_roster)
        cls.bot_profile_cursor += 1
        return cls.bot_profile_roster[index]

    def test_check_bots(self, bots: List[Bot]):
        time.sleep(2.0)

        assert len(bots) == 10

        group_counts = Counter(b.var.participant_group for b in bots)
        assert group_counts == {"A": 5, "B": 5}

        profile_counts = Counter(b.var.bot_profile for b in bots)
        assert profile_counts == BOT_PROFILE_COUNTS

        trials_by_profile = defaultdict(list)

        for b in bots:
            assert len(b.alive_trials) == 7  # 4 normal trials + 3 repeat trials
            assert all([t.finalized for t in b.alive_trials])
            assert {t.var.profile_metadata["bot_profile"] for t in b.alive_trials} == {
                b.var.bot_profile
            }

            for trial in b.alive_trials:
                metadata = trial.var.profile_metadata
                assert metadata["participant_id"] == b.id
                assert metadata["target"] in TARGETS
                assert metadata["active_channel"] in COLORS
                assert metadata["starting_values"] == trial.initial_vector
                assert metadata["submitted_channel_response"] == trial.answer
                assert isinstance(trial.answer, int)
                assert 0 <= trial.answer <= 255
                trials_by_profile[b.var.bot_profile].append(metadata)

        processes = AsyncProcess.query.all()
        assert all([not p.failed for p in processes])

        random_responses = [
            trial["submitted_channel_response"] for trial in trials_by_profile["random"]
        ]
        normal_distances = [
            trial["response_distance_from_start"]
            for trial in trials_by_profile["normal_rgb"]
        ]
        summary = {
            "target_profile_counts": BOT_PROFILE_COUNTS,
            "observed_profile_counts": dict(profile_counts),
            "participant_group_counts": dict(group_counts),
            "completed_participant_ids_by_profile": {
                profile: [b.id for b in bots if b.var.bot_profile == profile]
                for profile in BOT_PROFILE_COUNTS
            },
            "color_trial_count_by_profile": {
                profile: len(trials) for profile, trials in trials_by_profile.items()
            },
            "random_response_range": [
                min(random_responses),
                max(random_responses),
            ],
            "normal_rgb_mean_abs_distance_from_start": sum(normal_distances)
            / len(normal_distances),
        }
        logger.info("Observed bot profile summary: %s", json.dumps(summary, indent=2))

        evidence_path = os.environ.get("GIBBS_PROFILE_SUMMARY_PATH")
        if evidence_path:
            with open(evidence_path, "w") as f:
                json.dump(summary, f, indent=2)
                f.write("\n")

        super().test_check_bots(bots)
