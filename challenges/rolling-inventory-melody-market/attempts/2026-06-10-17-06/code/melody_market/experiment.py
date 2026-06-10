# pylint: disable=abstract-method,unused-argument

import copy
import json
import random
from typing import Any

from markupsafe import Markup

import psynet.experiment
from psynet.bot import Bot
from psynet.consent import MainConsent
from psynet.modular_page import Control, ModularPage, Prompt, SurveyJSControl
from psynet.page import InfoPage, SuccessfulEndPage
from psynet.timeline import CodeBlock, Event, FailedValidation, PageMaker, Timeline, join
from psynet.trial.chain import ChainNode
from psynet.trial.imitation_chain import ImitationChainTrial, ImitationChainTrialMaker
from psynet.utils import get_logger


logger = get_logger()

MELODY_LENGTH = 9
PITCH_LABELS = ["Do", "Re", "Mi"]
PITCH_COLORS = ["#2f80ed", "#27ae60", "#eb5757"]
NUM_EDITS = 3
NUM_EDITS_SEED = MELODY_LENGTH

MOUSE_SAMPLING_INTERVAL_MS = 250
MAX_MOUSE_POSITIONS = 500

POOL_SIZE = 12
N_CREATORS_PER_GENERATION = 1
N_SEED_IMAGES = 1
N_CHAINS = 16 * 2
N_TRIALS_PER_PARTICIPANT = 8
N_GENERATIONS = 7 * POOL_SIZE
DURATION_ESTIMATE = 11 * 60
PAYMENT = 2.25


def empty_melody() -> list[int | None]:
    return [None for _ in range(MELODY_LENGTH)]


def validate_melody_shape(melody: Any) -> list[int | None] | None:
    if not isinstance(melody, list) or len(melody) != MELODY_LENGTH:
        return None

    validated = []
    for value in melody:
        if value in (None, "", -1):
            validated.append(None)
        elif value in (0, 1, 2):
            validated.append(int(value))
        else:
            return None
    return validated


def melody_edit_distance(a: list[int | None], b: list[int | None]) -> int:
    return sum(1 for x, y in zip(a, b) if x != y)


def melody_is_empty(melody: list[int | None]) -> bool:
    return all(note is None for note in melody)


def mutate_melody(melody: list[int | None]) -> list[int | None]:
    edited = list(melody)
    slot = random.randrange(MELODY_LENGTH)
    current = edited[slot]
    choices = [None, 0, 1, 2]
    choices.remove(current)
    edited[slot] = random.choice(choices)
    if melody_is_empty(edited):
        edited[slot] = random.choice([0, 1, 2])
    return edited


class MelodyNode(ChainNode):
    """Rolling-inventory node for short melody artefacts."""

    def __init__(self, condition: str | None = None, **kwargs):
        super().__init__(**kwargs, participant_group=condition)

    def create_initial_seed(self, experiment=None, participant=None):
        return {
            "generation": 0,
            "options": [],
            "children": {},
            "proposed": {},
            "adoption_enabled": False,
            "melody": None,
        }

    def create_definition_from_seed(self, seed, experiment, participant):
        return seed

    def summarize_trials(self, trials, experiment, participant):
        definition = copy.deepcopy(self.seed)
        trial = trials[0]
        trial_id = trial.id

        melody_answers = {
            key: trial.answer[key] for key in trial.answer if "edit" in key
        }
        melody = melody_answers[sorted(melody_answers.keys())[-1]]
        definition["melody"] = melody

        for key, value in trial.answer.items():
            if "adopt" not in key or value is None:
                continue

            adopted_id = str(int(value))
            definition["children"].setdefault(adopted_id, []).append(str(trial_id))
            for item in definition["options"]:
                definition["proposed"][str(item)] = (
                    definition["proposed"].get(str(item), 0) + 1
                )
            break

        definition["options"].append(trial_id)
        definition["options"] = definition["options"][-POOL_SIZE:]
        definition["children"][str(trial_id)] = []
        definition["proposed"][str(trial_id)] = 0
        definition["adoption_enabled"] = len(definition["options"]) >= N_SEED_IMAGES
        definition["generation"] += 1

        return definition


class MelodyEditControl(Control):
    macro = "melody_edit_control"
    external_template = "melody-edit.html"

    def __init__(
        self,
        prefill_melody=None,
        num_edits: int = NUM_EDITS,
        mouse_sampling_interval_ms: int = MOUSE_SAMPLING_INTERVAL_MS,
        max_mouse_positions: int = MAX_MOUSE_POSITIONS,
        **kwargs,
    ):
        self.prefill_melody = validate_melody_shape(prefill_melody) or empty_melody()
        self.num_edits = num_edits
        self.mouse_sampling_interval_ms = mouse_sampling_interval_ms
        self.max_mouse_positions = max_mouse_positions
        self.user_events = []
        self.mouse = None
        self.mouse_positions = None
        super().__init__(**kwargs, bot_response=self.bot_response())

    def bot_response(self):
        if melody_is_empty(self.prefill_melody):
            melody = empty_melody()
            for slot in random.sample(range(MELODY_LENGTH), 4):
                melody[slot] = random.choice([0, 1, 2])
            return {"edit": melody, "events": [], "mouse": None, "mouse_positions": []}
        return {
            "edit": mutate_melody(self.prefill_melody),
            "events": [],
            "mouse": None,
            "mouse_positions": [],
        }

    def update_events(self, events):
        events["minimalTime"] = Event(is_triggered_by="trialStart", delay=5.0)
        events["submitEnable"].add_trigger("minimalTime")

    def format_answer(self, raw_answer, **kwargs):
        if isinstance(raw_answer, dict):
            self.user_events = raw_answer.get("events", [])
            self.mouse = raw_answer.get("mouse")
            self.mouse_positions = raw_answer.get("mouse_positions")
            raw_answer = raw_answer.get("edit")
        melody = validate_melody_shape(raw_answer)
        return melody if melody is not None else "INVALID_RESPONSE"

    def validate(self, response, **kwargs):
        if response.answer == "INVALID_RESPONSE":
            return FailedValidation("Please submit a valid melody.")

        melody = response.answer
        if melody_is_empty(melody):
            return FailedValidation("Please add at least one note to your melody.")

        n_changes = melody_edit_distance(melody, self.prefill_melody)
        if n_changes > self.num_edits:
            return FailedValidation(
                f"Please make no more than {self.num_edits} note changes."
            )
        if n_changes == 0:
            return FailedValidation("Please change at least one note before submitting.")
        return None

    @property
    def metadata(self):
        return {
            "melody_length": MELODY_LENGTH,
            "pitch_labels": PITCH_LABELS,
            "pitch_colors": PITCH_COLORS,
            "prefill_melody": self.prefill_melody,
            "num_edits": self.num_edits,
            "user_events": self.user_events,
            "mouse": self.mouse,
            "mouse_positions": self.mouse_positions,
        }


class MelodySelectControl(Control):
    macro = "melody_select_control"
    external_template = "melody-select.html"

    def __init__(
        self,
        proposals_data,
        choices,
        active_generation,
        display_popularity,
        mouse_sampling_interval_ms: int = MOUSE_SAMPLING_INTERVAL_MS,
        max_mouse_positions: int = MAX_MOUSE_POSITIONS,
        **kwargs,
    ):
        self.proposals_data = proposals_data
        self.choices = choices
        self.active_generation = active_generation
        self.display_popularity = display_popularity
        self.mouse_sampling_interval_ms = mouse_sampling_interval_ms
        self.max_mouse_positions = max_mouse_positions
        self.user_events = []
        self.mouse = None
        self.mouse_positions = None
        super().__init__(**kwargs, bot_response=self.bot_response())

    def bot_response(self):
        return {
            "adopt": random.choice(self.choices) if self.choices else None,
            "events": [],
            "mouse": None,
            "mouse_positions": [],
        }

    def update_events(self, events):
        events["minimalTime"] = Event(is_triggered_by="trialStart", delay=2.0)
        events["submitEnable"].add_trigger("minimalTime")

    def format_answer(self, raw_answer, **kwargs):
        if isinstance(raw_answer, dict):
            self.user_events = raw_answer.get("events", [])
            self.mouse = raw_answer.get("mouse")
            self.mouse_positions = raw_answer.get("mouse_positions")
            return raw_answer.get("adopt")
        return raw_answer

    def validate(self, response, **kwargs):
        if response.answer not in self.choices:
            return FailedValidation("Please choose a melody before continuing.")
        return None

    @property
    def metadata(self):
        return {
            "proposals_data": self.proposals_data,
            "choices": self.choices,
            "active_generation": self.active_generation,
            "display_popularity": self.display_popularity,
            "user_events": self.user_events,
            "mouse": self.mouse,
            "mouse_positions": self.mouse_positions,
        }


class CustomSurveyJSControl(SurveyJSControl):
    external_template = "custom_survey_js.html"

    def __init__(
        self,
        *args,
        mouse_sampling_interval_ms: int = MOUSE_SAMPLING_INTERVAL_MS,
        max_mouse_positions: int = MAX_MOUSE_POSITIONS,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.mouse_sampling_interval_ms = mouse_sampling_interval_ms
        self.max_mouse_positions = max_mouse_positions
        self.user_events = []
        self.mouse = None
        self.mouse_positions = None

    def format_answer(self, raw_answer, **kwargs):
        data = json.loads(raw_answer) if isinstance(raw_answer, str) else raw_answer
        if isinstance(data, dict) and "survey" in data:
            self.user_events = data.get("events", [])
            self.mouse = data.get("mouse")
            self.mouse_positions = data.get("mouse_positions")
            return data["survey"]
        return data

    @property
    def metadata(self):
        return {
            "user_events": self.user_events,
            "mouse": self.mouse,
            "mouse_positions": self.mouse_positions,
        }


class MelodyInputPage(ModularPage):
    def __init__(
        self,
        label: str,
        prompt: Markup,
        time_estimate: float,
        prefill_melody=None,
        num_edits: int = NUM_EDITS,
    ):
        super().__init__(
            label,
            Prompt(prompt),
            control=MelodyEditControl(
                prefill_melody=prefill_melody,
                num_edits=num_edits,
            ),
            time_estimate=time_estimate,
        )


class MelodyCreateTrial(ImitationChainTrial):
    time_estimate = 60
    accumulate_answers = True

    def first_trial(self):
        return InfoPage(
            "This market is empty for now. You will create a new melody from scratch.",
            time_estimate=10,
        )

    def other_trial(self):
        assert self.network.participant_group in ["pi", "npi"]
        display_popularity = self.network.participant_group == "pi"
        active_generation = self.definition["generation"]

        pool = self.query.filter(self.__class__.id.in_(self.definition["options"])).all()
        assert len(pool) <= POOL_SIZE

        children_dict = self.definition.get("children", {})
        roots = set(children_dict.keys())
        for parent in children_dict:
            roots -= set(children_dict[parent])

        order = []

        def dfs(node_id):
            order.append(node_id)
            children = list(children_dict.get(node_id, []))
            random.shuffle(children)
            for child in children:
                dfs(child)

        roots = list(roots)
        random.shuffle(roots)
        for root in roots:
            dfs(root)

        for proposal in pool:
            if str(proposal.id) not in order:
                raise RuntimeError("Pool item was not found in the ancestry tree.")

        pool = sorted(pool, key=lambda item: order.index(str(item.id)))

        proposals_data = []
        for index, proposal in enumerate(pool):
            proposal_data = {
                "id": proposal.id,
                "melody": proposal.answer["edit"],
                "label": chr(65 + index),
                "adopted_by": len(self.definition["children"].get(str(proposal.id), [])),
                "proposed_to": self.definition["proposed"].get(str(proposal.id), 0),
            }
            proposals_data.append(proposal_data)

        choices = [proposal.id for proposal in pool]

        return ModularPage(
            label="adopt",
            prompt=Markup(
                "<h3>Choose a melody to start from</h3>"
                "<p>You can listen to all melodies currently on the market"
                f"{' and see how often each one was selected by earlier participants' if display_popularity else ''}.</p>"
                f"<p>Choose one melody. On the next page, you may change up to {NUM_EDITS} notes.</p>"
                "<p>Your new melody will be added to the market inventory.</p>"
            ),
            control=MelodySelectControl(
                proposals_data=proposals_data,
                choices=choices,
                active_generation=active_generation,
                display_popularity=display_popularity,
            ),
            time_estimate=30,
            save_answer="adopt",
        )

    def adopt_page(self):
        if len(self.definition["options"]) < N_SEED_IMAGES:
            return [self.first_trial()]
        return [self.other_trial()]

    def edit_page(self, participant):
        if not self.definition["adoption_enabled"]:
            prefill_melody = empty_melody()
        else:
            adopt_id = participant.var.get("adopt")
            try:
                adopt_proposal = self.query.filter_by(id=adopt_id).one()
                prefill_melody = adopt_proposal.answer["edit"]
            except Exception:
                logger.warning("Could not load adopted melody %s; using empty melody.", adopt_id)
                prefill_melody = empty_melody()

        empty = melody_is_empty(prefill_melody)
        if empty:
            prompt = Markup(
                "<h3>Compose a melody</h3>"
                f"<p>Click the sequencer cells to add up to {MELODY_LENGTH} notes. "
                "Try to make a melody that future participants will want to build on.</p>"
            )
            max_edits = NUM_EDITS_SEED
        else:
            prompt = Markup(
                "<h3>Edit the adopted melody</h3>"
                f"<p>You may make up to {NUM_EDITS} note changes. "
                "Try to improve the melody so others select it from the market.</p>"
            )
            max_edits = NUM_EDITS

        return MelodyInputPage(
            "edit",
            prompt,
            time_estimate=30,
            prefill_melody=prefill_melody,
            num_edits=max_edits,
        )

    def show_trial(self, experiment, participant):
        return join(
            self.adopt_page(),
            PageMaker(self.edit_page, time_estimate=30),
        )


class MelodyTrialMaker(ImitationChainTrialMaker):
    pass


nodes = [
    MelodyNode(condition=["pi", "npi"][index % 2])
    for index in range(N_CHAINS)
]


def choose_participant_group(participant):
    return participant.var.get("condition")


trial_maker = MelodyTrialMaker(
    start_nodes=nodes,
    node_class=MelodyNode,
    trial_class=MelodyCreateTrial,
    id_="melody_trial_maker",
    chain_type="across",
    expected_trials_per_participant=N_TRIALS_PER_PARTICIPANT,
    max_trials_per_participant=N_TRIALS_PER_PARTICIPANT,
    chains_per_experiment=N_CHAINS,
    balance_across_chains=True,
    check_performance_at_end=True,
    check_performance_every_trial=False,
    propagate_failure=False,
    recruit_mode="n_trials",
    target_n_participants=None,
    wait_for_networks=False,
    max_nodes_per_chain=N_GENERATIONS,
    allow_revisiting_networks_in_across_chains=False,
    trials_per_node=N_CREATORS_PER_GENERATION,
    choose_participant_group=choose_participant_group,
)


def instructions(popularity_information):
    popularity_clause = (
        " and the popularity history for each melody"
        if popularity_information
        else ""
    )
    return join(
        InfoPage(
            Markup(
                "<h3>The melody market</h3>"
                "<p>In this experiment, you will compose short melodies that compete on a shared market.</p>"
                "<p>Each round has two steps: first you choose an existing melody, then you edit it or create a new one.</p>"
                "<h4>Selection step</h4>"
                f"<p>You will hear the melodies currently in the market{popularity_clause}. "
                "Select one melody to build on.</p>"
            ),
            time_estimate=25,
        ),
        InfoPage(
            Markup(
                "<h4>Creation step</h4>"
                "<p>The melody editor has three pitch rows: Mi, Re, and Do. "
                "Each of the nine time slots can contain at most one note.</p>"
                "<p>Use <strong>Play melody</strong> to hear your current sequence before submitting. "
                "Your submitted melody enters the market, and the oldest market item drops out once the inventory is full.</p>"
            ),
            time_estimate=25,
        ),
    )


post_survey = ModularPage(
    "survey",
    "Please tell us about your experience playing this experiment.",
    CustomSurveyJSControl(
        {
            "pages": [
                {
                    "name": "survey",
                    "elements": [
                        {
                            "type": "comment",
                            "name": "adoption_strategy",
                            "title": "Can you describe your strategy for choosing melodies to select? What did you listen for?",
                            "isRequired": True,
                        },
                        {
                            "type": "comment",
                            "name": "editing_strategy",
                            "title": "Can you describe your strategy when composing or editing melodies?",
                            "isRequired": True,
                        },
                        {
                            "type": "comment",
                            "name": "others",
                            "title": "What do you believe determines which melodies other participants tend to select?",
                            "isRequired": True,
                        },
                        {
                            "type": "comment",
                            "name": "freetext",
                            "title": "Did you encounter any issue or bug? Were the instructions clear?",
                            "isRequired": False,
                        },
                    ],
                }
            ],
            "headerView": "advanced",
        },
        bot_response=lambda: {
            "adoption_strategy": "I selected melodies with clear contours.",
            "editing_strategy": "I changed one or two notes to make a pattern.",
            "others": "People may choose memorable melodies.",
        },
    ),
    time_estimate=75,
)


def _(s):
    return s


class Exp(psynet.experiment.Experiment):
    label = "Rolling inventory melody market"
    test_n_bots = 16
    test_mode = "serial"

    config = {
        "recruiter": "generic",
        "wage_per_hour": 9,
        "currency": "$",
        "show_reward": False,
        "title": _(
            f"Melody market experiment (Chrome browser, ~{round(DURATION_ESTIMATE / 60)} minutes to complete)"
        ),
        "description": " ".join(
            [
                _("This experiment requires you to compose short melodies."),
                _(
                    "We recommend using Chrome in an incognito window, because some browser add-ons can interfere with experiments."
                ),
                _("If you have questions or concerns, please contact the research team."),
            ]
        ),
        "contact_email_on_error": "computational.audition@example.invalid",
        "organization_name": "Computational Audition Lab",
        "initial_recruitment_size": 3,
        "auto_recruit": False,
    }

    timeline = Timeline(
        MainConsent(),
        CodeBlock(
            lambda participant: participant.var.set(
                "condition", "pi" if participant.id % 2 else "npi"
            )
        ),
        CodeBlock(
            lambda participant: participant.var.set(
                "current_condition", participant.var.get("condition")
            )
        ),
        PageMaker(
            lambda participant: instructions(participant.var.get("condition") == "pi"),
            time_estimate=30,
        ),
        trial_maker,
        post_survey,
        SuccessfulEndPage(),
    )

    def test_check_bot(self, bot: Bot, **kwargs):
        assert len(bot.alive_trials) == N_TRIALS_PER_PARTICIPANT
        for trial in bot.alive_trials:
            assert "edit" in trial.answer
            assert validate_melody_shape(trial.answer["edit"]) is not None
