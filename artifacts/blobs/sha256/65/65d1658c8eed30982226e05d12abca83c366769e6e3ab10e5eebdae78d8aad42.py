import base64
import html
import json
import os
from dataclasses import asdict, dataclass
from typing import Any
from xml.etree import ElementTree

from markupsafe import Markup

import psynet.experiment
from psynet.bot import Bot
from psynet.modular_page import (
    ModularPage,
    Prompt,
    RadioButtonControl,
    RatingControl,
    TextControl,
)
from psynet.page import InfoPage
from psynet.timeline import CodeBlock, PageMaker, Timeline, join

REFERENCE_IMAGES = {
    "cat": {
        "label": "Cat",
        "path": "/static/references/cat.svg",
        "features": ["round face", "pointed ears", "whiskers", "warm orange fur"],
    },
    "penguin": {
        "label": "Penguin",
        "path": "/static/references/penguin.svg",
        "features": ["black body", "white belly", "orange beak", "flippers"],
    },
    "giraffe": {
        "label": "Giraffe",
        "path": "/static/references/giraffe.svg",
        "features": ["long neck", "brown spots", "ossicones", "yellow coat"],
    },
}

ROLE_CONDITIONS = {
    "human_led": {
        "label": "Human-led",
        "instructor_human_probability": 1.0,
        "selector_human_probability": 1.0,
        "description": "Humans write guidance and make comparison choices.",
    },
    "ai_led": {
        "label": "AI-led",
        "instructor_human_probability": 0.0,
        "selector_human_probability": 0.0,
        "description": "Mock AI writes guidance and makes comparison choices.",
    },
    "hybrid": {
        "label": "Hybrid",
        "instructor_human_probability": 0.5,
        "selector_human_probability": 0.5,
        "description": "Instructor and selector roles can be human or AI by configured probability.",
    },
}

DEMO_ITERATIONS = 3
SVG_TAGS = {"svg", "rect", "circle", "ellipse", "path", "line", "polyline", "polygon", "g", "text"}
SVG_ATTRS = {
    "xmlns",
    "viewBox",
    "role",
    "aria-label",
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
    "r",
    "rx",
    "ry",
    "d",
    "points",
    "fill",
    "stroke",
    "stroke-width",
    "stroke-linecap",
    "stroke-linejoin",
    "transform",
    "font-size",
    "text-anchor",
    "opacity",
}


@dataclass
class GenerationTask:
    reference_id: str
    reference_label: str
    reference_features: list[str]
    chain_id: str
    condition: str
    iteration: int
    instructor_role: str
    guidance: str
    previous_svg: str | None


@dataclass
class GenerationResult:
    svg_id: str
    svg_code: str
    model_name: str
    provider_mode: str
    prompt_metadata: dict[str, Any]
    generation_settings: dict[str, Any]
    render_state: dict[str, Any]


class SVGGeneratorClient:
    """Interface for mock or real SVG generation providers."""

    provider_mode = "interface"
    model_name = "abstract-svg-generator"

    def generate(self, task: GenerationTask) -> GenerationResult:  # pragma: no cover - interface
        raise NotImplementedError


class MockSVGGenerator(SVGGeneratorClient):
    provider_mode = "mock"
    model_name = "deterministic-mock-svg-generator-v1"

    def generate(self, task: GenerationTask) -> GenerationResult:
        svg = build_mock_svg(task.reference_id, task.iteration, task.guidance)
        return GenerationResult(
            svg_id=f"{task.chain_id}-i{task.iteration}-mock",
            svg_code=svg,
            model_name=self.model_name,
            provider_mode=self.provider_mode,
            prompt_metadata={
                "reference_id": task.reference_id,
                "reference_label": task.reference_label,
                "reference_features": task.reference_features,
                "has_previous_svg": task.previous_svg is not None,
                "guidance": task.guidance,
            },
            generation_settings={"temperature": 0.0, "max_iterations": DEMO_ITERATIONS},
            render_state=render_state(svg),
        )


class EnvironmentSVGGenerator(SVGGeneratorClient):
    provider_mode = "real-provider-placeholder"
    model_name = os.environ.get("SVG_GENERATOR_MODEL", "not-configured")

    def generate(self, task: GenerationTask) -> GenerationResult:
        raise RuntimeError(
            "Real provider mode is intentionally not implemented in this local demo. "
            "Set up a private client outside this repository if API credentials are deliberately supplied."
        )


def get_generator() -> SVGGeneratorClient:
    if os.environ.get("SVG_GENERATOR_PROVIDER", "mock").lower() == "mock":
        return MockSVGGenerator()
    return EnvironmentSVGGenerator()


def build_mock_svg(reference_id: str, iteration: int, guidance: str) -> str:
    palette = {
        "cat": ("#f6c36a", "#2a2a2a", "#fff4db"),
        "penguin": ("#242735", "#f2a51a", "#fff7e8"),
        "giraffe": ("#e7b558", "#8b572a", "#fff8e6"),
    }[reference_id]
    main, accent, light = palette
    guidance_l = guidance.lower()
    include_detail = iteration >= 2 or any(word in guidance_l for word in ["detail", "whisker", "spot", "flipper", "ear"])
    include_refinement = iteration >= 3 or any(word in guidance_l for word in ["closer", "match", "polish"])
    if reference_id == "cat":
        detail = "<path d='M78 103 H45 M80 116 H50 M162 103 H195 M160 116 H190' stroke='#111' stroke-width='4' stroke-linecap='round'/>" if include_detail else ""
        refine = "<path d='M82 55 L93 25 L107 62 Z M134 62 L149 25 L160 55 Z' fill='{0}' stroke='{1}' stroke-width='4'/>".format(main, accent) if include_refinement else ""
        body = f"<circle cx='120' cy='93' r='50' fill='{main}' stroke='{accent}' stroke-width='5'/>{refine}<circle cx='101' cy='86' r='7' fill='#111'/><circle cx='139' cy='86' r='7' fill='#111'/>{detail}<path d='M116 105 Q120 112 124 105' fill='none' stroke='#111' stroke-width='4'/>"
    elif reference_id == "penguin":
        detail = "<path d='M77 119 C48 120 51 84 86 88 M163 119 C192 120 189 84 154 88' fill='#242735'/>" if include_detail else ""
        refine = "<path d='M112 78 L128 78 L120 91 Z' fill='#f2a51a'/>" if include_refinement else ""
        body = f"<ellipse cx='120' cy='100' rx='48' ry='60' fill='{main}'/><ellipse cx='120' cy='111' rx='31' ry='41' fill='{light}'/><circle cx='103' cy='63' r='6' fill='#fff'/><circle cx='137' cy='63' r='6' fill='#fff'/>{refine}{detail}<path d='M92 160 L76 171 H111 Z M147 160 L130 171 H164 Z' fill='{accent}'/>"
    else:
        detail = "<circle cx='116' cy='91' r='8'/><circle cx='136' cy='113' r='7'/><circle cx='102' cy='130' r='6'/><circle cx='145' cy='145' r='8'/>" if include_detail else ""
        refine = "<path d='M96 43 L87 22 M136 38 L141 17' stroke='#4b3420' stroke-width='5' stroke-linecap='round'/><circle cx='87' cy='21' r='6'/><circle cx='141' cy='17' r='6'/>" if include_refinement else ""
        body = f"<path d='M94 157 L102 80 C105 50 143 49 148 80 L157 157 Z' fill='{main}' stroke='#4b3420' stroke-width='5'/><ellipse cx='124' cy='59' rx='40' ry='26' fill='{main}' stroke='#4b3420' stroke-width='5'/><circle cx='110' cy='56' r='5' fill='#111'/><circle cx='139' cy='56' r='5' fill='#111'/><g fill='{accent}'>{detail}{refine}</g>"
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 240 180' role='img' aria-label='mock {html.escape(reference_id)} iteration {iteration}'><rect width='240' height='180' fill='#f7fbff'/>{body}</svg>"


def sanitize_svg(svg_code: str) -> tuple[str | None, str | None]:
    try:
        root = ElementTree.fromstring(svg_code)
    except ElementTree.ParseError as exc:
        return None, f"parse_error: {exc}"
    for element in root.iter():
        tag = element.tag.split("}", 1)[-1]
        if tag not in SVG_TAGS:
            return None, f"disallowed_tag: {tag}"
        for attr in list(element.attrib):
            attr_name = attr.split("}", 1)[-1]
            if attr_name.lower().startswith("on") or attr_name not in SVG_ATTRS:
                return None, f"disallowed_attr: {attr_name}"
    return ElementTree.tostring(root, encoding="unicode"), None


def render_state(svg_code: str) -> dict[str, Any]:
    sanitized, error = sanitize_svg(svg_code)
    return {"ok": sanitized is not None, "error": error}


def svg_img(svg_code: str | None, alt: str) -> str:
    if not svg_code:
        return "<div class='svg-error'>No SVG rendition yet.</div>"
    sanitized, error = sanitize_svg(svg_code)
    if error:
        return f"<div class='svg-error'>SVG render error: {html.escape(error)}</div>"
    encoded = base64.b64encode(sanitized.encode("utf-8")).decode("ascii")
    return f"<img class='svg-card-image' alt='{html.escape(alt)}' src='data:image/svg+xml;base64,{encoded}'>"


def reference_img(reference_id: str) -> str:
    ref = REFERENCE_IMAGES[reference_id]
    return f"<img class='svg-card-image' alt='{html.escape(ref['label'])} reference image' src='{ref['path']}'>"


def panel(title: str, body: str) -> str:
    return f"<section class='svg-card'><h3>{html.escape(title)}</h3>{body}</section>"


def page_styles() -> str:
    return """
    <style>
      .vibe-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; align-items: stretch; margin: 1rem 0; }
      .svg-card { border: 1px solid #d4d8df; border-radius: 12px; padding: 0.75rem; background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.05); }
      .svg-card h3 { margin-top: 0; font-size: 1rem; }
      .svg-card-image { width: 100%; max-height: 230px; object-fit: contain; background: #f8fafc; border-radius: 8px; }
      .svg-error { padding: 2rem; background: #fff1f2; color: #9f1239; border-radius: 8px; }
      .vibe-note { color: #475569; font-size: 0.95rem; }
    </style>
    """


def current_state(participant) -> dict[str, Any]:
    return participant.var.get("human_chain_state")


def chain_records(participant) -> list[dict[str, Any]]:
    return participant.var.get("chain_records", default=[])


def set_chain_records(participant, records: list[dict[str, Any]]) -> None:
    participant.var.set("chain_records", records)


def init_participant(participant) -> None:
    participant.var.set("role_conditions", ROLE_CONDITIONS)
    participant.var.set(
        "human_chain_state",
        {
            "chain_id": "human-cat-demo",
            "condition": "human_led",
            "reference_id": "cat",
            "best_svg_id": None,
            "best_svg": None,
            "last_candidate": None,
        },
    )
    participant.var.set("chain_records", [])
    participant.var.set("condition_summaries", simulate_condition_summaries())


def instructor_prompt(participant, iteration: int) -> Markup:
    state = current_state(participant)
    reference_id = state["reference_id"]
    previous = state.get("best_svg")
    previous_panel = panel("Current best SVG rendition", svg_img(previous, "current best SVG")) if previous else panel("Current best SVG rendition", "<p class='vibe-note'>No SVG has been generated yet. Start by describing the most important visual structure.</p>")
    html_body = f"""
    {page_styles()}
    <h2>Iteration {iteration} of {DEMO_ITERATIONS}: guide the SVG generator</h2>
    <p>Write high-level natural-language guidance for a coding assistant. Focus on what would make the SVG match the reference image more closely; you do not need to write SVG code.</p>
    <div class='vibe-grid'>
      {panel('Reference image', reference_img(reference_id))}
      {previous_panel}
    </div>
    """
    return Markup(html_body)


def selector_prompt(participant, iteration: int) -> Markup:
    state = current_state(participant)
    reference_id = state["reference_id"]
    candidate = state["last_candidate"]
    html_body = f"""
    {page_styles()}
    <h2>Iteration {iteration}: choose the SVG to carry forward</h2>
    <p>Compare the previous best rendition with the newly generated rendition. Choose the SVG that better matches the reference image.</p>
    <div class='vibe-grid'>
      {panel('Reference image', reference_img(reference_id))}
      {panel('Previous best', svg_img(state.get('best_svg'), 'previous best SVG'))}
      {panel('Newly generated candidate', svg_img(candidate['svg_code'], 'new SVG candidate'))}
    </div>
    """
    return Markup(html_body)


def evaluator_prompt(participant) -> Markup:
    state = current_state(participant)
    html_body = f"""
    {page_styles()}
    <h2>Independent similarity rating</h2>
    <p>Now act as an evaluator. Rate only the visual similarity between the reference image and the final SVG rendition. Do not use the chain condition, prompts, or model metadata.</p>
    <div class='vibe-grid'>
      {panel('Reference image', reference_img(state['reference_id']))}
      {panel('Generated SVG rendition', svg_img(state.get('best_svg'), 'final generated SVG'))}
    </div>
    """
    return Markup(html_body)


def make_task(participant, iteration: int, guidance: str, instructor_role: str) -> GenerationTask:
    state = current_state(participant)
    ref = REFERENCE_IMAGES[state["reference_id"]]
    return GenerationTask(
        reference_id=state["reference_id"],
        reference_label=ref["label"],
        reference_features=ref["features"],
        chain_id=state["chain_id"],
        condition=state["condition"],
        iteration=iteration,
        instructor_role=instructor_role,
        guidance=guidance,
        previous_svg=state.get("best_svg"),
    )


def generate_candidate(participant, iteration: int) -> None:
    guidance = participant.var.get(f"human_guidance_{iteration}")
    task = make_task(participant, iteration, guidance, "human")
    result = get_generator().generate(task)
    state = current_state(participant)
    state["last_candidate"] = asdict(result)
    participant.var.set("human_chain_state", state)


def finalize_iteration(participant, iteration: int, choice: str, selector_role: str, reasoning: str) -> None:
    state = current_state(participant)
    candidate = state["last_candidate"]
    previous_svg = state.get("best_svg")
    previous_svg_id = state.get("best_svg_id")
    selected_current = choice == "current" or previous_svg is None
    selected_svg = candidate["svg_code"] if selected_current else previous_svg
    selected_svg_id = candidate["svg_id"] if selected_current else previous_svg_id
    state["best_svg"] = selected_svg
    state["best_svg_id"] = selected_svg_id
    participant.var.set("human_chain_state", state)
    record = {
        "reference_id": state["reference_id"],
        "chain_id": state["chain_id"],
        "condition": state["condition"],
        "iteration": iteration,
        "instructor_role": "human",
        "selector_role": selector_role,
        "guidance": participant.var.get(f"human_guidance_{iteration}"),
        "generated_svg_id": candidate["svg_id"],
        "generated_svg_code": candidate["svg_code"],
        "render_state": candidate["render_state"],
        "selector_choice": "current" if selected_current else "previous",
        "selector_reasoning": reasoning,
        "previous_svg_id": previous_svg_id,
        "selected_svg_id": selected_svg_id,
        "model_name": candidate["model_name"],
        "provider_mode": candidate["provider_mode"],
        "prompt_metadata": candidate["prompt_metadata"],
        "generation_settings": candidate["generation_settings"],
    }
    records = chain_records(participant)
    records.append(record)
    set_chain_records(participant, records)


def save_human_selection(participant) -> None:
    choice = participant.var.get("human_selection_3")
    reasoning = f"Human selector chose {choice} in the third iteration comparison."
    finalize_iteration(participant, 3, choice, "human", reasoning)


def save_evaluator_rating(participant) -> None:
    state = current_state(participant)
    participant.var.set(
        "evaluator_rating",
        {
            "reference_id": state["reference_id"],
            "svg_id": state["best_svg_id"],
            "rating_scale": "1 = not at all similar, 7 = extremely similar",
            "rating": participant.var.get("similarity_rating"),
            "condition_hidden_from_evaluator": True,
        },
    )


def ai_guidance(reference_id: str, iteration: int, previous_svg: str | None) -> str:
    features = ", ".join(REFERENCE_IMAGES[reference_id]["features"])
    base = f"Emphasize the {REFERENCE_IMAGES[reference_id]['label'].lower()} features: {features}."
    if previous_svg:
        return f"{base} Refine the current SVG so the silhouette and distinctive details match more closely."
    return f"{base} Start with a clear simple animal silhouette."


def role_for(condition: str, role: str, iteration: int) -> str:
    if role == "selector" and iteration < 3:
        return "not_applicable_before_selection_phase"
    if condition == "human_led":
        return "human"
    if condition == "ai_led":
        return "ai"
    pattern = {
        ("instructor", 1): "human",
        ("instructor", 2): "ai",
        ("instructor", 3): "human",
        ("selector", 1): "not_applicable_before_selection_phase",
        ("selector", 2): "not_applicable_before_selection_phase",
        ("selector", 3): "ai",
    }
    return pattern[(role, iteration)]


def simulate_chain(condition: str, reference_id: str) -> list[dict[str, Any]]:
    best_svg = None
    best_svg_id = None
    records = []
    client = MockSVGGenerator()
    for iteration in range(1, DEMO_ITERATIONS + 1):
        instructor_role = role_for(condition, "instructor", iteration)
        guidance = ai_guidance(reference_id, iteration, best_svg)
        if instructor_role == "human":
            guidance = f"Scripted local human guidance: {guidance}"
        task = GenerationTask(
            reference_id=reference_id,
            reference_label=REFERENCE_IMAGES[reference_id]["label"],
            reference_features=REFERENCE_IMAGES[reference_id]["features"],
            chain_id=f"{condition}-{reference_id}-demo",
            condition=condition,
            iteration=iteration,
            instructor_role=instructor_role,
            guidance=guidance,
            previous_svg=best_svg,
        )
        result = client.generate(task)
        selector_role = role_for(condition, "selector", iteration)
        previous_svg_id = best_svg_id
        selector_choice = "current"
        selected_svg = result.svg_code
        selected_svg_id = result.svg_id
        if iteration == 3 and condition == "hybrid":
            selector_choice = "current"
        best_svg = selected_svg
        best_svg_id = selected_svg_id
        records.append(
            {
                "reference_id": reference_id,
                "chain_id": task.chain_id,
                "condition": condition,
                "iteration": iteration,
                "instructor_role": instructor_role,
                "selector_role": selector_role,
                "guidance": guidance,
                "generated_svg_id": result.svg_id,
                "generated_svg_code": result.svg_code,
                "render_state": result.render_state,
                "selector_choice": selector_choice,
                "selector_reasoning": f"{selector_role} selector carried forward the current candidate in the deterministic demo.",
                "previous_svg_id": previous_svg_id,
                "selected_svg_id": selected_svg_id,
                "model_name": result.model_name,
                "provider_mode": result.provider_mode,
                "prompt_metadata": result.prompt_metadata,
                "generation_settings": result.generation_settings,
            }
        )
    return records


def simulate_condition_summaries() -> dict[str, Any]:
    return {
        condition: {
            "configuration": ROLE_CONDITIONS[condition],
            "records": simulate_chain(condition, reference_id),
        }
        for condition, reference_id in [("human_led", "cat"), ("ai_led", "penguin"), ("hybrid", "giraffe")]
    }


def summary_prompt(participant) -> Markup:
    state = current_state(participant)
    body = {
        "completed_human_chain_iterations": len(chain_records(participant)),
        "final_svg_id": state.get("best_svg_id"),
        "role_conditions_saved": list(participant.var.get("condition_summaries").keys()),
        "evaluator_rating": participant.var.get("evaluator_rating"),
        "mock_mode": True,
    }
    return Markup(f"<h2>Demo complete</h2><p>The chain state, role assignments, SVG render states, selector choices, and evaluator rating have been saved.</p><pre>{html.escape(json.dumps(body, indent=2))}</pre>")


def human_chain_timeline():
    return join(
        PageMaker(
            lambda participant: ModularPage(
                "human_guidance_1",
                instructor_prompt(participant, 1),
                TextControl(one_line=False, height="110px"),
                save_answer="human_guidance_1",
                bot_response="Start with a round orange cat face, pointed ears, eyes, and whiskers.",
                time_estimate=20,
            ),
            time_estimate=20,
        ),
        CodeBlock(lambda participant: generate_candidate(participant, 1)),
        CodeBlock(lambda participant: finalize_iteration(participant, 1, "current", "not_applicable_before_selection_phase", "First candidate starts the chain.")),
        PageMaker(
            lambda participant: ModularPage(
                "human_guidance_2",
                instructor_prompt(participant, 2),
                TextControl(one_line=False, height="110px"),
                save_answer="human_guidance_2",
                bot_response="Add more cat-specific details: longer whiskers, symmetrical ears, and a small nose.",
                time_estimate=20,
            ),
            time_estimate=20,
        ),
        CodeBlock(lambda participant: generate_candidate(participant, 2)),
        CodeBlock(lambda participant: finalize_iteration(participant, 2, "current", "not_applicable_before_selection_phase", "Second candidate becomes the current best before selection trials begin.")),
        PageMaker(
            lambda participant: ModularPage(
                "human_guidance_3",
                instructor_prompt(participant, 3),
                TextControl(one_line=False, height="110px"),
                save_answer="human_guidance_3",
                bot_response="Polish the face so it matches the reference: keep the orange fur, ears, eyes, nose, and whiskers clear.",
                time_estimate=20,
            ),
            time_estimate=20,
        ),
        CodeBlock(lambda participant: generate_candidate(participant, 3)),
        PageMaker(
            lambda participant: ModularPage(
                "human_selection_3",
                selector_prompt(participant, 3),
                RadioButtonControl(
                    choices=["previous", "current"],
                    labels=["Previous best SVG", "Newly generated SVG"],
                    name="svg_selection",
                    force_selection=True,
                ),
                save_answer="human_selection_3",
                bot_response="current",
                time_estimate=20,
            ),
            time_estimate=20,
        ),
        CodeBlock(save_human_selection),
    )


def get_timeline():
    return Timeline(
        InfoPage(
            Markup(
                "<h1>Collaborative SVG vibe coding</h1>"
                "<p>You will help a mock AI generator recreate a reference animal image as SVG. "
                "Across three iterations, write natural-language guidance; on the third iteration, choose which SVG should carry forward.</p>"
            ),
            time_estimate=10,
        ),
        CodeBlock(init_participant),
        human_chain_timeline(),
        PageMaker(
            lambda participant: ModularPage(
                "similarity_rating",
                evaluator_prompt(participant),
                RatingControl(
                    values=7,
                    min_description="Not at all similar",
                    max_description="Extremely similar",
                ),
                save_answer="similarity_rating",
                bot_response=6,
                time_estimate=15,
            ),
            time_estimate=15,
        ),
        CodeBlock(save_evaluator_rating),
        PageMaker(lambda participant: InfoPage(summary_prompt(participant), time_estimate=8), time_estimate=8),
    )


class Exp(psynet.experiment.Experiment):
    label = "Collaborative SVG vibe coding"
    test_n_bots = 2
    timeline = get_timeline()

    def test_check_bot(self, bot: Bot, **kwargs):
        super().test_check_bot(bot, **kwargs)
        assert not bot.failed
        records = bot.var.get("chain_records")
        assert len(records) == 3
        assert [record["iteration"] for record in records] == [1, 2, 3]
        assert records[2]["selector_role"] == "human"
        assert records[2]["selector_choice"] in {"previous", "current"}
        assert all(record["render_state"]["ok"] for record in records)
        condition_summaries = bot.var.get("condition_summaries")
        assert set(condition_summaries) == {"human_led", "ai_led", "hybrid"}
        assert condition_summaries["ai_led"]["records"][0]["instructor_role"] == "ai"
        assert condition_summaries["hybrid"]["records"][2]["selector_role"] == "ai"
        assert bot.var.get("evaluator_rating")["condition_hidden_from_evaluator"] is True
