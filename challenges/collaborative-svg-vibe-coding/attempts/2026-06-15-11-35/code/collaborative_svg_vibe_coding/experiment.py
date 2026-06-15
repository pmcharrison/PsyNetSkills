import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

from dominate import tags
from markupsafe import Markup

import psynet.experiment
from psynet.bot import Bot
from psynet.modular_page import Control, ModularPage, Prompt, RatingControl
from psynet.page import InfoPage
from psynet.timeline import FailedValidation, Timeline
from psynet.trial.imitation_chain import (
    ImitationChainNetwork,
    ImitationChainNode,
    ImitationChainTrial,
    ImitationChainTrialMaker,
)
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker


ElementTree.register_namespace("", "http://www.w3.org/2000/svg")

ROOT = Path(__file__).parent
REFERENCE_MANIFEST = ROOT / "static" / "references" / "manifest.json"
GENERATOR_SYSTEM_PROMPT = (
    "You are the code generator. Return only safe inline SVG code for the "
    "instructor's high-level instruction."
)
MOCK_PROVIDER_MODE = "mock"
MAX_SVG_CHARS = 6000
CHAIN_ITERATIONS = 3


ROLE_SCHEDULE = [
    {"condition": "human-led", "instructor_role": "human", "selector_role": "none"},
    {"condition": "hybrid", "instructor_role": "ai", "selector_role": "human"},
    {"condition": "ai-led", "instructor_role": "ai", "selector_role": "ai"},
]


SAFE_SVG_ELEMENTS = {
    "svg",
    "g",
    "circle",
    "ellipse",
    "rect",
    "path",
    "polygon",
    "polyline",
    "line",
    "text",
}
SAFE_SVG_ATTRIBUTES = {
    "xmlns",
    "viewBox",
    "width",
    "height",
    "x",
    "y",
    "x1",
    "y1",
    "x2",
    "y2",
    "cx",
    "cy",
    "rx",
    "ry",
    "r",
    "d",
    "points",
    "fill",
    "stroke",
    "stroke-width",
    "stroke-linecap",
    "stroke-linejoin",
    "opacity",
    "font-size",
    "font-family",
    "text-anchor",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def load_references():
    with REFERENCE_MANIFEST.open() as f:
        return json.load(f)


def reference_url(reference):
    return "/" + reference["path"]


def role_assignment(iteration):
    return deepcopy(ROLE_SCHEDULE[(iteration - 1) % len(ROLE_SCHEDULE)])


def svg_id(svg_code):
    return "svg_" + hashlib.sha256(svg_code.encode("utf8")).hexdigest()[:12]


def color_from_instruction(instruction, offset):
    digest = hashlib.sha256((instruction + str(offset)).encode("utf8")).hexdigest()
    return "#" + digest[:6]


def generate_svg_from_instruction(high_level_instruction):
    """Mock code generator: its only input is the high-level instruction."""
    instruction = high_level_instruction.strip() or "Make a simple animal SVG."
    body = color_from_instruction(instruction, 1)
    accent = color_from_instruction(instruction, 2)
    if any(word in instruction.lower() for word in ["refine", "sharper", "clearer"]):
        body = "#b9e6ff"
        accent = "#6f5bd8"
    eye = "#222222"
    whisker = "#4a3428"
    ear_shift = int(hashlib.sha256(instruction.encode("utf8")).hexdigest()[:2], 16) % 12
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 220" width="220" height="220">
  <rect width="220" height="220" rx="24" fill="#f8f3e8"/>
  <circle cx="110" cy="116" r="58" fill="{body}" stroke="#3d2b20" stroke-width="5"/>
  <polygon points="{62 + ear_shift},70 84,24 100,82" fill="{accent}" stroke="#3d2b20" stroke-width="5"/>
  <polygon points="{158 - ear_shift},70 136,24 120,82" fill="{accent}" stroke="#3d2b20" stroke-width="5"/>
  <circle cx="88" cy="106" r="8" fill="{eye}"/>
  <circle cx="132" cy="106" r="8" fill="{eye}"/>
  <ellipse cx="110" cy="128" rx="10" ry="7" fill="#f3b6ad"/>
  <path d="M110 136 C104 148 91 150 82 142" fill="none" stroke="#3d2b20" stroke-width="4" stroke-linecap="round"/>
  <path d="M110 136 C116 148 129 150 138 142" fill="none" stroke="#3d2b20" stroke-width="4" stroke-linecap="round"/>
  <line x1="72" y1="126" x2="28" y2="114" stroke="{whisker}" stroke-width="3" stroke-linecap="round"/>
  <line x1="74" y1="138" x2="30" y2="144" stroke="{whisker}" stroke-width="3" stroke-linecap="round"/>
  <line x1="148" y1="126" x2="192" y2="114" stroke="{whisker}" stroke-width="3" stroke-linecap="round"/>
  <line x1="146" y1="138" x2="190" y2="144" stroke="{whisker}" stroke-width="3" stroke-linecap="round"/>
</svg>"""


def ai_instruction(iteration):
    instructions = {
        2: "Draw a front-facing cat with triangular ears, round head, dark eyes, whiskers, and a warm background.",
        3: "Refine the SVG cat by making the ears sharper, the face more symmetrical, and the whiskers clearer.",
    }
    return instructions.get(iteration, "Create a clean SVG animal drawing with visible defining features.")


def sanitize_svg(svg_code):
    if not isinstance(svg_code, str) or not svg_code.strip():
        return False, "", "SVG code is empty."
    if len(svg_code) > MAX_SVG_CHARS:
        return False, "", "SVG code exceeds the local size limit."
    try:
        root = ElementTree.fromstring(svg_code)
    except ElementTree.ParseError as error:
        return False, "", f"SVG XML parse error: {error}."
    for element in root.iter():
        tag = element.tag.split("}", 1)[-1]
        if tag not in SAFE_SVG_ELEMENTS:
            return False, "", f"Disallowed SVG element: {tag}."
        for attr, value in element.attrib.items():
            attr_name = attr.split("}", 1)[-1]
            lowered = str(value).lower()
            if attr_name not in SAFE_SVG_ATTRIBUTES:
                return False, "", f"Disallowed SVG attribute: {attr_name}."
            if attr_name.startswith("on") or "javascript:" in lowered:
                return False, "", "Unsafe event handler or JavaScript URL."
            if "http://" in lowered or "https://" in lowered or "data:" in lowered:
                return False, "", "External or data URL references are not allowed."
    return True, ElementTree.tostring(root, encoding="unicode"), None


def enrich_vibe_answer(raw_answer, definition):
    answer = deepcopy(raw_answer)
    candidate_ok, candidate_svg, candidate_error = sanitize_svg(answer.get("candidate_svg"))
    selected_ok, selected_svg, selected_error = sanitize_svg(answer.get("selected_svg"))
    answer.update(
        {
            "reference_id": definition["reference_id"],
            "reference_url": definition["reference_url"],
            "chain_iteration": definition["iteration"],
            "condition": definition["condition"],
            "instructor_role": definition["instructor_role"],
            "selector_role": definition["selector_role"],
            "code_generator_role": "ai_mock",
            "provider_mode": MOCK_PROVIDER_MODE,
            "model_name": "deterministic-local-svg-generator",
            "prompt_metadata": {
                "system_prompt": GENERATOR_SYSTEM_PROMPT,
                "generator_visible_fields": ["system", "high_level_instruction"],
                "reference_id_visible_to_generator": False,
                "previous_svg_visible_to_generator": False,
                "iteration_visible_to_generator": False,
            },
            "previous_svg_id": definition.get("best_svg_id"),
            "candidate_svg": candidate_svg if candidate_ok else answer.get("candidate_svg", ""),
            "candidate_render_status": "rendered" if candidate_ok else "render_error",
            "candidate_render_error": candidate_error,
            "selected_svg": selected_svg if selected_ok else answer.get("selected_svg", ""),
            "selected_render_status": "rendered" if selected_ok else "render_error",
            "selected_render_error": selected_error,
            "generation_timestamp": utc_now(),
        }
    )
    if not answer.get("candidate_svg_id"):
        answer["candidate_svg_id"] = svg_id(answer["candidate_svg"])
    if not answer.get("selected_svg_id") and answer.get("selected_svg"):
        answer["selected_svg_id"] = svg_id(answer["selected_svg"])
    return answer


def unwrap_vibe_answer(answer):
    if isinstance(answer, dict):
        if "chain_iteration" in answer:
            return answer
        for key in ("collaborative_svg_iteration", "answer", "raw_answer"):
            if key in answer:
                return unwrap_vibe_answer(answer[key])
        for value in answer.values():
            if isinstance(value, dict):
                candidate = unwrap_vibe_answer(value)
                if isinstance(candidate, dict) and "chain_iteration" in candidate:
                    return candidate
    return answer


def initial_svg():
    return ""


def initial_definition(reference):
    iteration = 1
    roles = role_assignment(iteration)
    return {
        "reference_id": reference["reference_id"],
        "reference_url": reference_url(reference),
        "reference_source": reference["source"],
        "iteration": iteration,
        "condition": roles["condition"],
        "instructor_role": roles["instructor_role"],
        "selector_role": roles["selector_role"],
        "best_svg": initial_svg(),
        "best_svg_id": None,
        "previous_iteration": None,
    }


class VibePrompt(Prompt):
    macro = "vibe_prompt"
    external_template = "vibe-coding.html"

    def __init__(self, definition):
        super().__init__()
        self.definition = definition

    @property
    def metadata(self):
        return {
            "reference_id": self.definition["reference_id"],
            "iteration": self.definition["iteration"],
            "condition": self.definition["condition"],
            "instructor_role": self.definition["instructor_role"],
            "selector_role": self.definition["selector_role"],
        }


class VibeControl(Control):
    macro = "vibe_control"
    external_template = "vibe-coding.html"

    def __init__(self, definition):
        super().__init__(show_next_button=False)
        self.definition = definition
        self.system_prompt = GENERATOR_SYSTEM_PROMPT
        self.ai_instruction = ai_instruction(definition["iteration"])

    @property
    def metadata(self):
        return {
            "generator_system_prompt": self.system_prompt,
            "provider_mode": MOCK_PROVIDER_MODE,
            "mock_contract": "generator receives only system prompt and high-level instruction",
        }

    def get_bot_response(self, experiment, bot, page, prompt):
        instruction = (
            self.ai_instruction
            if self.definition["instructor_role"] == "ai"
            else "Make the SVG resemble the reference cat: pointed ears, rounded face, eyes, and whiskers."
        )
        candidate_svg = generate_svg_from_instruction(instruction)
        candidate_id = svg_id(candidate_svg)
        has_previous = bool(self.definition.get("best_svg"))
        selector_choice = "candidate"
        selected_svg = candidate_svg
        selected_svg_id = candidate_id
        if has_previous and self.definition["selector_role"] == "human":
            selector_choice = "previous"
            selected_svg = self.definition["best_svg"]
            selected_svg_id = self.definition["best_svg_id"]
        answer = {
            "guidance": instruction,
            "generator_prompt": {
                "system": self.system_prompt,
                "high_level_instruction": instruction,
            },
            "candidate_svg": candidate_svg,
            "candidate_svg_id": candidate_id,
            "candidate_render_status": "rendered",
            "selector_choice": selector_choice,
            "selector_reasoning": "Bot selected deterministically for local validation.",
            "selected_svg": selected_svg,
            "selected_svg_id": selected_svg_id,
        }
        return enrich_vibe_answer(answer, self.definition)

    def format_answer(self, raw_answer, **kwargs):
        return enrich_vibe_answer(raw_answer, kwargs["trial"].definition)

    def validate(self, response, **kwargs):
        answer = response.answer
        if not answer.get("guidance"):
            return FailedValidation("Please provide a high-level instruction.")
        if not answer.get("candidate_svg"):
            return FailedValidation("Generate an SVG candidate before submitting.")
        if not answer.get("selected_svg"):
            return FailedValidation("Choose which SVG should advance.")
        return None


class VibeNetwork(ImitationChainNetwork):
    pass


class VibeNode(ImitationChainNode):
    def create_initial_seed(self, experiment, participant):
        return initial_definition(load_references()[0])

    def make_next_definition(self, experiment, participant):
        answer = unwrap_vibe_answer(self.completed_and_processed_trials[0].answer)
        next_iteration = self.definition["iteration"] + 1
        roles = role_assignment(next_iteration)
        return {
            "reference_id": self.definition["reference_id"],
            "reference_url": self.definition["reference_url"],
            "reference_source": self.definition["reference_source"],
            "iteration": next_iteration,
            "condition": roles["condition"],
            "instructor_role": roles["instructor_role"],
            "selector_role": roles["selector_role"],
            "best_svg": answer["selected_svg"],
            "best_svg_id": answer["selected_svg_id"],
            "previous_iteration": {
                "chain_iteration": answer["chain_iteration"],
                "guidance": answer["guidance"],
                "candidate_svg_id": answer["candidate_svg_id"],
                "selected_svg_id": answer["selected_svg_id"],
                "selector_choice": answer["selector_choice"],
                "condition": answer["condition"],
                "instructor_role": answer["instructor_role"],
                "selector_role": answer["selector_role"],
            },
        }


class VibeTrial(ImitationChainTrial):
    time_estimate = 25

    def show_trial(self, experiment, participant):
        return ModularPage(
            "collaborative_svg_iteration",
            VibePrompt(self.definition),
            VibeControl(self.definition),
            time_estimate=self.time_estimate,
        )


class VibeTrialMaker(ImitationChainTrialMaker):
    response_timeout_sec = 120
    check_timeout_interval_sec = 30


def get_start_nodes(participant=None):
    return [VibeNode(definition=initial_definition(reference)) for reference in load_references()]


def evaluator_candidate_svg():
    return generate_svg_from_instruction(ai_instruction(3))


class EvaluatorPrompt(Prompt):
    macro = "evaluator_prompt"
    external_template = "vibe-coding.html"

    def __init__(self, definition):
        super().__init__()
        self.definition = definition

    @property
    def metadata(self):
        return {
            "reference_id": self.definition["reference_id"],
            "candidate_svg_id": self.definition["candidate_svg_id"],
            "condition_hidden": True,
        }


class EvaluatorTrial(StaticTrial):
    time_estimate = 15

    def show_trial(self, experiment, participant):
        return ModularPage(
            "independent_similarity_rating",
            EvaluatorPrompt(self.definition),
            RatingControl(
                values=7,
                min_description="Not similar",
                max_description="Very similar",
                bot_response=6,
            ),
            time_estimate=self.time_estimate,
        )

    def format_answer(self, raw_answer, **kwargs):
        return {
            "reference_id": self.definition["reference_id"],
            "reference_url": self.definition["reference_url"],
            "candidate_svg_id": self.definition["candidate_svg_id"],
            "similarity_rating": int(raw_answer),
            "condition_visible": False,
        }


def get_evaluator_nodes():
    reference = load_references()[0]
    candidate_svg = evaluator_candidate_svg()
    ok, sanitized_svg, error = sanitize_svg(candidate_svg)
    return [
        StaticNode(
            definition={
                "reference_id": reference["reference_id"],
                "reference_url": reference_url(reference),
                "candidate_svg": sanitized_svg if ok else candidate_svg,
                "candidate_svg_id": svg_id(candidate_svg),
                "render_status": "rendered" if ok else "render_error",
                "render_error": error,
            }
        )
    ]


def get_timeline():
    return Timeline(
        InfoPage(
            Markup(
                """
                <h2>Collaborative SVG vibe coding</h2>
                <p>You will guide a code generator to recreate a reference animal image as SVG.
                Write high-level instructions, compare SVG candidates, and choose what advances.</p>
                """
            ),
            time_estimate=5,
        ),
        VibeTrialMaker(
            id_="collaborative_svg_chain",
            network_class=VibeNetwork,
            trial_class=VibeTrial,
            node_class=VibeNode,
            chain_type="within",
            start_nodes=get_start_nodes,
            max_nodes_per_chain=CHAIN_ITERATIONS,
            max_trials_per_participant=CHAIN_ITERATIONS,
            expected_trials_per_participant=CHAIN_ITERATIONS,
            chains_per_participant=1,
            chains_per_experiment=None,
            trials_per_node=1,
            balance_across_chains=True,
            check_performance_at_end=False,
            check_performance_every_trial=False,
            recruit_mode="n_participants",
            target_n_participants=12,
        ),
        InfoPage(
            "Next you will complete an independent similarity-rating task. You will not see prompts or role labels.",
            time_estimate=4,
        ),
        StaticTrialMaker(
            id_="independent_similarity_evaluator",
            trial_class=EvaluatorTrial,
            nodes=get_evaluator_nodes,
            expected_trials_per_participant="n_nodes",
        ),
        InfoPage("Thank you. The local demonstration is complete.", time_estimate=3),
    )


class Exp(psynet.experiment.Experiment):
    label = "Collaborative SVG vibe coding"
    timeline = get_timeline()
    test_n_bots = 6
    test_mode = "serial"

    def test_check_bot(self, bot: Bot, **kwargs):
        super().test_check_bot(bot, **kwargs)
        chain_trials = [
            trial
            for trial in bot.alive_trials
            if getattr(trial, "trial_maker_id", None) == "collaborative_svg_chain"
        ]
        assert len(chain_trials) == CHAIN_ITERATIONS
        answers = [unwrap_vibe_answer(trial.answer) for trial in chain_trials]
        assert {answer["condition"] for answer in answers} == {
            "human-led",
            "hybrid",
            "ai-led",
        }
        for answer in answers:
            assert answer["generator_prompt"].keys() == {"system", "high_level_instruction"}
            assert answer["prompt_metadata"]["reference_id_visible_to_generator"] is False
            assert answer["candidate_render_status"] == "rendered"
            assert answer["selected_svg_id"]
        evaluator_trials = [
            trial
            for trial in bot.alive_trials
            if getattr(trial, "trial_maker_id", None) == "independent_similarity_evaluator"
        ]
        assert len(evaluator_trials) == 1
        assert evaluator_trials[0].answer["condition_visible"] is False
