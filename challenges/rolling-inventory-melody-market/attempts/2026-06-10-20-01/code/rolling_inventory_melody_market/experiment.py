# pylint: disable=unused-argument,abstract-method

import random
from typing import List

import numpy as np
import psynet.experiment
from markupsafe import Markup
from psynet.consent import MainConsent
from psynet.modular_page import Control, ModularPage, Prompt, SurveyJSControl
from psynet.page import InfoPage, SuccessfulEndPage, VolumeCalibration
from psynet.prescreen import HugginsHeadphoneTest
from psynet.timeline import CodeBlock, Event, FailedValidation, PageMaker, Timeline, join
from psynet.trial.chain import ChainNode
from psynet.trial.create_and_rate import CreateAndRateNodeMixin, CreateTrialMixin
from psynet.trial.imitation_chain import ImitationChainTrial, ImitationChainTrialMaker
from psynet.utils import get_logger

logger = get_logger()

NOTE_LABELS = ["Mi", "Re", "Do"]
NOTE_FREQUENCIES = [329.63, 293.66, 261.63]
N_ROWS = len(NOTE_LABELS)
N_STEPS = 9
NUM_EDITS = 5
NUM_EDITS_SEED = 12

POOL_SIZE = 12
N_CREATORS_PER_GENERATION = 1
N_SEED_IMAGES = 1
N_CHAINS = 16 * 2
N_TRIALS_PER_PARTICIPANT = 8
N_GENERATIONS = 7 * POOL_SIZE
DURATION_ESTIMATE = 11 * 60
PAYMENT = 2.25


def empty_melody():
    return [[0 for _ in range(N_STEPS)] for _ in range(N_ROWS)]


def default_seed_melody(chain_id):
    melody = empty_melody()
    offset = (chain_id or 0) % N_ROWS
    for step in range(0, N_STEPS, 2):
        melody[(step + offset) % N_ROWS][step] = 1
    return melody


def melody_change_count(melody, reference):
    return int(np.sum(np.abs(np.array(melody, dtype=int) - np.array(reference, dtype=int))))


def melody_to_waveform(melody, samples_per_step=8):
    """Downsample the synthesized melody into deterministic waveform peaks."""
    waveform = []
    step_duration = 0.22
    sub_samples = 24
    melody_array = np.array(melody, dtype=int)
    for step in range(N_STEPS):
        active_rows = [row for row in range(N_ROWS) if melody_array[row, step] == 1]
        for display_sample in range(samples_per_step):
            peak = 0.0
            for sub_sample in range(sub_samples):
                pos = (display_sample + (sub_sample + 0.5) / sub_samples) / samples_per_step
                envelope = np.sin(np.pi * pos)
                t = (step + pos) * step_duration
                value = 0.0
                for row in active_rows:
                    value += np.sin(2 * np.pi * NOTE_FREQUENCIES[row] * t)
                peak = max(peak, abs(value) * envelope / max(1, len(active_rows)))
            waveform.append(peak)
    peak = max(waveform) if waveform else 0.0
    if peak <= 0:
        return [0.0 for _ in waveform]
    return [float(round(value / peak, 3)) for value in waveform]


def latest_melody_from_answer(answer):
    if not isinstance(answer, dict):
        return empty_melody()
    melodies = {key: value for key, value in answer.items() if "edit" in key}
    if not melodies:
        return empty_melody()
    return melodies[sorted(melodies.keys())[-1]]


headphones_warning = InfoPage(
    Markup(
        """
        <h3>Attention</h3>
        <hr>
        <b><b>You must use headphones or earplugs</b></b>.
        <br><br>
        If you do not, the experiment will terminate early.
        <hr>
        """
    ),
    time_estimate=3,
)


class MelodyNode(ChainNode, CreateAndRateNodeMixin):
    def __init__(self, condition: str = None, **kwargs):
        kwargs["context"] = {
            "note_labels": NOTE_LABELS,
            "note_frequencies": NOTE_FREQUENCIES,
            "n_steps": N_STEPS,
        }
        super().__init__(**kwargs, participant_group=condition)

    def create_initial_seed(self, experiment=None, participant=None):
        return {
            "generation": 0,
            "options": [],
            "children": {},
            "proposed": {},
            "adoption_enabled": False,
            "inventory_updates": [],
        }

    def create_definition_from_seed(self, seed, experiment, participant):
        return seed

    def summarize_trials(self, trials, experiment, participant):
        definition = self.seed.copy()
        trial = trials[0]
        trial_id = trial.id
        adopted_id = None

        melody = latest_melody_from_answer(trial.answer)
        definition["melody"] = melody

        for key, value in trial.answer.items():
            if "adopt" in key and value is not None:
                adopted_id = int(value)
                definition["children"].setdefault(str(adopted_id), []).append(str(trial_id))
                for item in definition["options"]:
                    definition["proposed"][str(item)] = definition["proposed"].get(str(item), 0) + 1
                break

        previous_options = list(definition["options"])
        definition["options"].append(trial_id)
        definition["options"] = definition["options"][-POOL_SIZE:]
        definition["children"][str(trial_id)] = []
        definition["proposed"][str(trial_id)] = 0
        definition["adoption_enabled"] = len(definition["options"]) >= N_SEED_IMAGES
        definition["generation"] += 1
        definition["inventory_updates"].append(
            {
                "trial_id": trial_id,
                "adopted_id": adopted_id,
                "previous_options": previous_options,
                "new_options": list(definition["options"]),
                "generation": definition["generation"],
            }
        )
        return definition

    def __repr__(self):
        return "MelodyNode(3x9)"


class MelodyEditorControl(Control):
    macro = "melody_editor_control"
    external_template = "melody-editor.html"

    def __init__(self, prefill_melody=None, num_edits=NUM_EDITS, chain_id=None, **kwargs):
        self.prefill_melody = prefill_melody or empty_melody()
        self.num_edits = num_edits
        self.chain_id = chain_id
        self.note_labels = NOTE_LABELS
        self.note_frequencies = NOTE_FREQUENCIES
        self.n_steps = N_STEPS
        super().__init__(**kwargs, bot_response=self.bot_response())

    def bot_response(self):
        melody = np.array(self.prefill_melody, dtype=int)
        if int(np.sum(melody)) == 0:
            return default_seed_melody(self.chain_id)

        possible = [(row, step) for row in range(N_ROWS) for step in range(N_STEPS)]
        random.shuffle(possible)
        for row, step in possible[: max(1, min(self.num_edits, 2))]:
            melody[row, step] = 1 - melody[row, step]
        return melody.tolist()

    def update_events(self, events):
        events["minimalTime"] = Event(is_triggered_by="trialStart", delay=1.0)
        events["submitEnable"].add_trigger("minimalTime")

    def format_answer(self, raw_answer, **kwargs):
        if isinstance(raw_answer, dict):
            melody = raw_answer.get("edit", raw_answer)
        else:
            melody = raw_answer
        return self._validate_melody(melody)

    def _validate_melody(self, melody):
        if not isinstance(melody, list) or len(melody) != N_ROWS:
            return "INVALID_RESPONSE"
        validated = []
        for row in melody:
            if not isinstance(row, list) or len(row) != N_STEPS:
                return "INVALID_RESPONSE"
            validated.append([1 if cell == 1 else 0 for cell in row])
        return validated

    def validate(self, response, **kwargs):
        if response.answer == "INVALID_RESPONSE":
            return FailedValidation("Please submit a valid melody.")
        if int(np.sum(response.answer)) == 0:
            return FailedValidation("Please create a non-empty melody.")
        n_changes = melody_change_count(response.answer, self.prefill_melody)
        if n_changes == 0:
            return FailedValidation("Please change at least one note before submitting.")
        if n_changes > self.num_edits:
            return FailedValidation(f"Please make no more than {self.num_edits} note changes.")
        return None

    @property
    def metadata(self):
        return {
            "prefill_melody": self.prefill_melody,
            "num_edits": self.num_edits,
            "note_labels": NOTE_LABELS,
            "note_frequencies": NOTE_FREQUENCIES,
            "n_steps": N_STEPS,
        }


class MelodySelectControl(Control):
    macro = "melody_select_control"
    external_template = "melody-selection.html"

    def __init__(self, proposals_data, choices, active_generation, display_popularity, **kwargs):
        self.proposals_data = proposals_data
        self.choices = choices
        self.active_generation = active_generation
        self.display_popularity = display_popularity
        self.note_labels = NOTE_LABELS
        self.note_frequencies = NOTE_FREQUENCIES
        self.n_steps = N_STEPS
        super().__init__(**kwargs, bot_response=self.bot_response())

    def format_answer(self, raw_answer, **kwargs):
        if isinstance(raw_answer, dict):
            return raw_answer.get("adopt")
        return raw_answer

    def validate(self, response, **kwargs):
        if response.answer not in self.choices:
            return FailedValidation("Please choose one melody before continuing.")
        return None

    def update_events(self, events):
        events["minimalTime"] = Event(is_triggered_by="trialStart", delay=1.0)
        events["submitEnable"].add_trigger("minimalTime")

    def bot_response(self):
        return random.choice(self.choices) if self.choices else None

    @property
    def metadata(self):
        return {
            "proposals_data": self.proposals_data,
            "choices": self.choices,
            "active_generation": self.active_generation,
            "display_popularity": self.display_popularity,
            "note_labels": NOTE_LABELS,
            "note_frequencies": NOTE_FREQUENCIES,
            "n_steps": N_STEPS,
        }


class MelodyInputPage(ModularPage):
    def __init__(self, label: str, prompt: Markup, prefill_melody=None, num_edits=NUM_EDITS, chain_id=None):
        super().__init__(
            label,
            Prompt(prompt),
            control=MelodyEditorControl(
                prefill_melody=prefill_melody,
                num_edits=num_edits,
                chain_id=chain_id,
            ),
            time_estimate=30,
        )


class MelodyCreateTrial(CreateTrialMixin, ImitationChainTrial):
    time_estimate = 60
    accumulate_answers = True

    def first_trial(self):
        return InfoPage(
            "This market is empty for now. You will compose a new melody from scratch.",
            time_estimate=5,
        )

    def ordered_pool(self):
        pool = self.query.filter(self.__class__.id.in_(self.definition["options"])).all()
        assert len(pool) <= POOL_SIZE, "Pool must contain POOL_SIZE elements at most"
        children = self.definition.get("children", {})
        roots = set(children.keys())
        for parent in children:
            roots -= set(children[parent])

        order = []

        def dfs(node_id):
            order.append(node_id)
            child_ids = list(children.get(node_id, []))
            random.shuffle(child_ids)
            for child_id in child_ids:
                dfs(child_id)

        roots = list(roots)
        random.shuffle(roots)
        for root in roots:
            dfs(root)

        for proposal in pool:
            if str(proposal.id) not in order:
                order.append(str(proposal.id))
        return sorted(pool, key=lambda item: order.index(str(item.id)))

    def other_trial(self):
        assert self.network.participant_group in ["pi", "npi"], "Participant group must be pi or npi"
        active_generation = self.definition["generation"]
        display_popularity = self.network.participant_group == "pi"
        pool = self.ordered_pool()
        proposals_data = []

        for i, proposal in enumerate(pool):
            melody = latest_melody_from_answer(proposal.answer)
            proposals_data.append(
                {
                    "id": proposal.id,
                    "melody": melody,
                    "waveform": melody_to_waveform(melody),
                    "label": chr(65 + i),
                    "adopted_by": len(self.definition["children"].get(str(proposal.id), [])),
                    "proposed_to": self.definition["proposed"].get(str(proposal.id), 0),
                }
            )

        return ModularPage(
            label="adopt",
            prompt=Prompt(
                Markup(
                    f"<h3>Choose a melody to start from</h3>"
                    f"<p>You can listen to all melodies on the market{' and how many times they were selected by other participants' if display_popularity else ''}.</p>"
                    f"<p>Choose a melody. On the next page, you will be allowed to change up to {NUM_EDITS} notes.</p>"
                    "<p>Your creation will be added to the inventory. Try to have it selected by others as many times as possible!</p>"
                )
            ),
            control=MelodySelectControl(
                proposals_data=proposals_data,
                choices=[proposal.id for proposal in pool],
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
        adoption_enabled = self.definition["adoption_enabled"]
        if adoption_enabled:
            adopt_id = participant.var.get("adopt")
            try:
                adopt_proposal = self.query.filter_by(id=adopt_id).one()
                prefill_melody = latest_melody_from_answer(adopt_proposal.answer)
            except Exception:
                prefill_melody = empty_melody()
        else:
            prefill_melody = empty_melody()

        from_scratch = int(np.sum(prefill_melody)) == 0
        if from_scratch:
            prompt = Markup(
                f"""
                <h3>Compose a new melody</h3>
                <p>Turn notes on and off in the step sequencer. You may add up to {NUM_EDITS_SEED} notes.</p>
                <p>Use <strong>Play melody</strong> to preview your creation before submitting it.</p>
                """
            )
        else:
            prompt = Markup(
                f"""
                <h3>Edit the melody you selected</h3>
                <p>You may make up to {NUM_EDITS} note changes. Try to make a version that future participants will choose.</p>
                <p>Use <strong>Play melody</strong> to compare the edited sequence with what you want to submit.</p>
                """
            )

        return MelodyInputPage(
            "edit",
            prompt,
            prefill_melody=prefill_melody,
            num_edits=NUM_EDITS_SEED if from_scratch else NUM_EDITS,
            chain_id=self.network_id,
        )

    def show_trial(self, experiment, participant):
        return join(
            self.adopt_page(),
            PageMaker(self.edit_page, time_estimate=30),
        )


class MelodyTrialMaker(ImitationChainTrialMaker):
    pass


nodes = [
    MelodyNode(condition=["pi", "npi"][i % 2])
    for i in range(N_CHAINS)
]


def choose_participant_group(participant):
    return participant.var.get("condition")


trial_maker_selection = MelodyTrialMaker(
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
    popularity_text = " and see how often each melody has been selected" if popularity_information else ""
    return join(
        InfoPage(
            Markup(
                f"""
                <h3>The melody market</h3>
                <p>In this experiment, you will compose short melodies that compete in a shared market.</p>
                <p>Each round has two steps: first you listen to market melodies{popularity_text}, then you create your own version.</p>
                <p>When the market is empty, you will skip selection and compose from scratch.</p>
                """
            ),
            time_estimate=20,
        ),
        InfoPage(
            Markup(
                """
                <h3>Composing melodies</h3>
                <p>The editor has three pitch rows: <strong>Mi</strong>, <strong>Re</strong>, and <strong>Do</strong>, plus nine time slots.</p>
                <p>Click cells to turn notes on or off. More than one pitch can play in the same time slot.</p>
                <p>Preview your sequence with <strong>Play melody</strong>, then submit it to the market.</p>
                """
            ),
            time_estimate=20,
        ),
    )


post_survey = ModularPage(
    "survey",
    "Please tell us about your experience playing this melody market.",
    SurveyJSControl(
        {
            "pages": [
                {
                    "name": "survey",
                    "elements": [
                        {
                            "type": "comment",
                            "name": "adoption_strategy",
                            "title": "Can you describe your strategy for choosing among melodies to select?",
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
                            "title": "What do you believe dictates which melodies other participants tend to select?",
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
        }
    ),
    time_estimate=60,
    bot_response=lambda: {
        "adoption_strategy": "I chose memorable melodies.",
        "editing_strategy": "I changed a small number of notes.",
        "others": "People may select clear rhythmic patterns.",
    },
)


class Exp(psynet.experiment.Experiment):
    label = "Rolling inventory melody market"
    test_n_bots = 16
    test_mode = "serial"

    config = {
        "initial_recruitment_size": 3,
    }

    timeline = Timeline(
        MainConsent(),
        headphones_warning,
        VolumeCalibration(),
        HugginsHeadphoneTest(),
        InfoPage("You passed the headphone screening task! Congratulations.", time_estimate=3),
        CodeBlock(lambda participant: participant.var.set("condition", "pi" if participant.id % 2 else "npi")),
        CodeBlock(lambda participant: participant.var.set("current_condition", participant.var.get("condition"))),
        PageMaker(
            lambda participant: instructions(participant.var.get("condition") == "pi"),
            time_estimate=30,
        ),
        trial_maker_selection,
        post_survey,
        SuccessfulEndPage(),
    )

    def test_check_bot(self, bot, **kwargs):
        assert not bot.failed
        trials = MelodyCreateTrial.query.filter_by(participant_id=bot.id).all()
        assert len(trials) == N_TRIALS_PER_PARTICIPANT
        for trial in trials:
            melody = latest_melody_from_answer(trial.answer)
            assert len(melody) == N_ROWS
            assert len(melody[0]) == N_STEPS
            assert int(np.sum(melody)) > 0

    def test_experiment(self):
        super().test_experiment()
        trials = MelodyCreateTrial.query.all()
        assert len(trials) == self.test_n_bots * N_TRIALS_PER_PARTICIPANT
        adopted_trials = [trial for trial in trials if trial.answer.get("adopt") is not None]
        assert adopted_trials, "At least one bot should complete an adoption round."
        for node in MelodyNode.query.all():
            assert len(node.definition["options"]) <= POOL_SIZE
            assert "adoption_enabled" in node.definition


if __name__ == "__main__":
    print(f"Experiment: {Exp.label}")
    print(f"Chains: {N_CHAINS}; trials per participant: {N_TRIALS_PER_PARTICIPANT}; pool size: {POOL_SIZE}")
    print(f"Sequencer: {N_ROWS} rows x {N_STEPS} steps ({', '.join(NOTE_LABELS)})")
