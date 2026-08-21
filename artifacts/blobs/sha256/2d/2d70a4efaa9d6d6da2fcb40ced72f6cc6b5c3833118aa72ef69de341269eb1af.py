import os
import random
import tempfile
import time
from collections import Counter
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
from psynet.field import extra_var
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
RANDOM_PROFILE = "random"
NORMAL_RGB_PROFILE = "normal_rgb"
BOT_PROFILES = [RANDOM_PROFILE, NORMAL_RGB_PROFILE]
TEST_N_BOTS = 10
NORMAL_RGB_SD = 20


def clamp_rgb_channel(value):
    return max(0, min(255, int(round(value))))


def make_balanced_profile_roster(n_bots, rng):
    if n_bots % len(BOT_PROFILES) != 0:
        raise ValueError("The bot count must divide evenly across response profiles.")

    n_per_profile = n_bots // len(BOT_PROFILES)
    roster = [profile for profile in BOT_PROFILES for _ in range(n_per_profile)]
    rng.shuffle(roster)
    return roster


def get_bot_profile(participant):
    if participant is None:
        return None
    return participant.var.get("bot_profile", None)


def sample_color_bot_response(bot, trial):
    profile = get_bot_profile(bot)
    active_index = trial.active_index
    starting_values = trial.initial_vector

    if profile == RANDOM_PROFILE:
        response = random.randint(0, 255)
    elif profile == NORMAL_RGB_PROFILE:
        response = clamp_rgb_channel(random.gauss(starting_values[active_index], NORMAL_RGB_SD))
    else:
        raise ValueError(f"Unknown bot profile: {profile}")

    return BotResponse(
        answer=response,
        metadata={
            "bot_profile": profile,
            "target": trial.context["target"],
            "active_index": active_index,
            "active_color": COLORS[active_index],
            "starting_values": starting_values,
            "submitted_channel_response": response,
        },
    )


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
                bot_response=sample_color_bot_response,
            ),
            time_estimate=time_estimate,
        )

    def metadata(self, participant=None, answer=None, **kwargs):
        trial = participant.current_trial if participant is not None else None
        return {
            "prompt": self.prompt.metadata,
            "bot_profile": get_bot_profile(participant),
            "target": trial.context["target"] if trial is not None else None,
            "selected_idx": self.selected_idx,
            "active_color": COLORS[self.selected_idx],
            "starting_values": self.starting_values,
            "submitted_channel_response": answer,
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
    __extra_vars__ = GibbsTrial.__extra_vars__.copy()

    run_async_post_trial = True
    resample_free_parameter = True
    time_estimate = 5

    @property
    @extra_var(__extra_vars__)
    def target(self):
        return self.context["target"]

    @property
    @extra_var(__extra_vars__)
    def active_color(self):
        return COLORS[self.active_index]

    @property
    @extra_var(__extra_vars__)
    def bot_profile(self):
        return get_bot_profile(self.participant)

    @property
    @extra_var(__extra_vars__)
    def submitted_channel_response(self):
        return self.answer

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
    trials_per_node=3,  # Supports the required 10-bot simulation without changing per-participant trial flow.
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

    test_n_bots = TEST_N_BOTS

    def initialize_bot(self, bot):
        if not hasattr(self, "_bot_profile_rng"):
            seed = os.environ.get("BOT_PROFILE_SEED")
            self._bot_profile_rng = random.Random(seed)
            self._bot_profile_roster = []
            self._bot_profile_assignment_index = 0

        if self._bot_profile_assignment_index >= len(self._bot_profile_roster):
            self._bot_profile_roster.extend(
                make_balanced_profile_roster(TEST_N_BOTS, self._bot_profile_rng)
            )

        profile = self._bot_profile_roster[self._bot_profile_assignment_index]
        bot.var.bot_profile = profile
        bot.var.bot_profile_assignment_index = self._bot_profile_assignment_index
        self._bot_profile_assignment_index += 1

    def test_check_bots(self, bots: List[Bot]):
        time.sleep(2.0)

        assert len(bots) == TEST_N_BOTS
        assert len([b for b in bots if b.var.participant_group == "A"]) == 5
        assert len([b for b in bots if b.var.participant_group == "B"]) == 5

        profile_counts = Counter(b.var.bot_profile for b in bots)
        assert profile_counts == Counter({RANDOM_PROFILE: 5, NORMAL_RGB_PROFILE: 5})
        print(
            "Observed participant profile distribution from completed bots: "
            f"{dict(sorted(profile_counts.items()))}"
        )

        for b in bots:
            assert len(b.alive_trials) == 7  # 4 normal trials + 3 repeat trials
            assert all([t.finalized for t in b.alive_trials])
            assert len({t.bot_profile for t in b.alive_trials}) == 1
            assert all(t.bot_profile == b.var.bot_profile for t in b.alive_trials)
            for trial in b.alive_trials:
                assert isinstance(trial.answer, int)
                assert 0 <= trial.answer <= 255
                assert trial.response.metadata["bot_profile"] == b.var.bot_profile
                assert trial.response.metadata["target"] == trial.context["target"]
                assert trial.response.metadata["active_color"] == COLORS[trial.active_index]
                assert trial.response.metadata["starting_values"] == trial.initial_vector
                assert (
                    trial.response.metadata["submitted_channel_response"] == trial.answer
                )

        processes = AsyncProcess.query.all()
        assert all([not p.failed for p in processes])

        super().test_check_bots(bots)
