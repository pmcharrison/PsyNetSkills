# pylint: disable=unused-argument,abstract-method

import html
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import psynet.experiment
from markupsafe import Markup
from psynet.bot import Bot
from psynet.modular_page import ModularPage, RadioButtonControl, TextControl
from psynet.page import InfoPage
from psynet.timeline import PageMaker, Timeline, join
from psynet.trial.imitation_chain import (
    ImitationChainNetwork,
    ImitationChainNode,
    ImitationChainTrial,
    ImitationChainTrialMaker,
)
from psynet.utils import get_logger

logger = get_logger()

PORTFOLIO_TASK = (
    "Create a polished one-page portfolio website for Alex Morgan, a fictional "
    "product designer. The page should introduce Alex, describe selected work, "
    "highlight skills, and include a concise contact section."
)

DEFAULT_MODEL = "openai/gpt-4o-mini"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
SAFE_EMPTY_WEBSITE = """
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Portfolio draft unavailable</title></head>
<body>
  <main>
    <h1>Portfolio draft unavailable</h1>
    <p>The AI response did not contain usable website HTML.</p>
  </main>
</body>
</html>
""".strip()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def openrouter_config() -> Dict[str, Any]:
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    return {
        "api_key_present": bool(api_key),
        "api_key": api_key,
        "base_url": os.getenv("OPENROUTER_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        "model": os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL),
        "timeout_seconds": float(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "20")),
    }


def strip_secret_config(config: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "api_key_present": config["api_key_present"],
        "base_url": config["base_url"],
        "model": config["model"],
        "timeout_seconds": config["timeout_seconds"],
    }


def normalize_website_html(raw_text: str) -> Dict[str, Any]:
    raw_text = (raw_text or "").strip()
    warnings = []

    if not raw_text:
        return {
            "html": SAFE_EMPTY_WEBSITE,
            "warnings": ["empty_response"],
            "used_repair": True,
        }

    fenced = re.search(r"```(?:html)?\s*(.*?)```", raw_text, flags=re.DOTALL | re.I)
    if fenced:
        raw_text = fenced.group(1).strip()
        warnings.append("extracted_html_code_fence")

    html_match = re.search(r"(<html[\s\S]*?</html>)", raw_text, flags=re.I)
    if html_match:
        raw_text = html_match.group(1)
    elif "<" not in raw_text or ">" not in raw_text:
        raw_text = (
            "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<title>Portfolio draft</title></head><body><main>"
            f"<p>{html.escape(raw_text)}</p>"
            "</main></body></html>"
        )
        warnings.append("wrapped_plain_text")

    sanitized = re.sub(
        r"<script\b[^>]*>[\s\S]*?</script>", "", raw_text, flags=re.I
    )
    sanitized = re.sub(r"\son\w+\s*=\s*(['\"]).*?\1", "", sanitized, flags=re.I)
    sanitized = re.sub(r"\sjavascript:", " ", sanitized, flags=re.I)

    if sanitized != raw_text:
        warnings.append("removed_active_content")

    if "<html" not in sanitized.lower():
        sanitized = (
            "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<title>Portfolio draft</title></head><body>"
            f"{sanitized}</body></html>"
        )
        warnings.append("wrapped_fragment")

    return {
        "html": sanitized,
        "warnings": warnings,
        "used_repair": bool(warnings),
    }


def website_iframe(website_html: str, title: str) -> str:
    escaped_title = html.escape(title, quote=True)
    escaped_srcdoc = html.escape(website_html or SAFE_EMPTY_WEBSITE, quote=True)
    return (
        "<div class='portfolio-frame'>"
        f"<h3>{escaped_title}</h3>"
        "<iframe sandbox='' referrerpolicy='no-referrer' "
        "style='width:100%; min-height:360px; border:1px solid #bbb; "
        "border-radius:8px; background:white;' "
        f"title='{escaped_title}' srcdoc=\"{escaped_srcdoc}\"></iframe>"
        "</div>"
    )


def website_pair(current_html: str, earlier_html: str) -> str:
    return (
        "<div style='display:grid; grid-template-columns:1fr 1fr; gap:1rem;'>"
        f"{website_iframe(current_html, 'Website A: previous round')}"
        f"{website_iframe(earlier_html, 'Website B: two rounds earlier')}"
        "</div>"
    )


def get_previous_website(definition: Dict[str, Any]) -> Optional[str]:
    return definition.get("generated_website")


def get_parent_definition(node) -> Optional[Dict[str, Any]]:
    if node.parent is None:
        return None
    return node.parent.definition


def get_grandparent_definition(node) -> Optional[Dict[str, Any]]:
    parent = node.parent
    if parent is None or parent.parent is None:
        return None
    return parent.parent.definition


def build_messages(participant_instruction: str, website_context: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are an expert frontend designer. Return only a complete, "
                "self-contained HTML document for a one-page portfolio website. "
                "Do not include markdown fences."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Original task:\n{PORTFOLIO_TASK}\n\n"
                f"Context to build from:\n{website_context}\n\n"
                f"Participant instruction:\n{participant_instruction}\n\n"
                "Return the next website version as a complete HTML document with "
                "inline CSS and no external scripts."
            ),
        },
    ]


def check_model_available(config: Dict[str, Any]) -> Dict[str, Any]:
    if not config["api_key_present"]:
        return {"available": False, "reason": "api_key_missing"}

    request = urllib.request.Request(
        f"{config['base_url']}/models",
        headers={"Authorization": f"Bearer {config['api_key']}"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(
            request, timeout=config["timeout_seconds"]
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"available": False, "reason": f"model_check_failed:{exc}"}

    model_ids = [model.get("id") for model in payload.get("data", [])]
    if config["model"] not in model_ids:
        return {
            "available": False,
            "reason": f"model_unavailable:{config['model']}",
            "model_count": len(model_ids),
        }

    return {"available": True, "reason": None, "model_count": len(model_ids)}


def call_openrouter(
    participant_instruction: str, website_context: str
) -> Dict[str, Any]:
    config = openrouter_config()
    messages = build_messages(participant_instruction, website_context)
    request_payload = {
        "model": config["model"],
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 2500,
    }
    availability = check_model_available(config)

    if not availability["available"]:
        return fallback_ai_response(
            participant_instruction,
            website_context,
            request_payload,
            strip_secret_config(config),
            availability["reason"],
            availability,
        )

    request = urllib.request.Request(
        f"{config['base_url']}/chat/completions",
        data=json.dumps(request_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/pmcharrison/PsyNetSkills",
            "X-Title": "PsyNetSkills portfolio website chain",
        },
        method="POST",
    )

    try:
        started_at = time.time()
        with urllib.request.urlopen(
            request, timeout=config["timeout_seconds"]
        ) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
        elapsed = time.time() - started_at
        raw_text = (
            response_payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        normalized = normalize_website_html(raw_text)
        return {
            "backend": "openrouter",
            "fallback_reason": None,
            "ai_request_payload": request_payload,
            "ai_request_config": strip_secret_config(config),
            "model_availability": availability,
            "ai_response_payload": response_payload,
            "raw_ai_response": raw_text,
            "generated_website": normalized["html"],
            "normalization": normalized,
            "elapsed_seconds": elapsed,
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
        return fallback_ai_response(
            participant_instruction,
            website_context,
            request_payload,
            strip_secret_config(config),
            f"live_call_failed:{exc}",
            availability,
        )


def fallback_ai_response(
    participant_instruction: str,
    website_context: str,
    request_payload: Dict[str, Any],
    request_config: Dict[str, Any],
    fallback_reason: str,
    availability: Dict[str, Any],
) -> Dict[str, Any]:
    safe_instruction = html.escape(participant_instruction)
    safe_context = html.escape(website_context[:600])
    generated = f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Alex Morgan Portfolio</title>
  <style>
    body {{ margin: 0; font-family: Inter, Arial, sans-serif; color: #18202a; }}
    main {{ max-width: 960px; margin: 0 auto; padding: 48px 24px; }}
    header {{ background: linear-gradient(135deg, #264653, #2a9d8f); color: white; padding: 52px 32px; border-radius: 24px; }}
    section {{ margin-top: 32px; padding: 24px; border: 1px solid #d9e2ec; border-radius: 18px; }}
    .tag {{ display: inline-block; margin: 4px; padding: 6px 10px; background: #e9f5f3; border-radius: 999px; }}
  </style>
</head>
<body>
  <main>
    <header>
      <p>Product Designer</p>
      <h1>Alex Morgan</h1>
      <p>Designing focused digital products for research, learning, and creative teams.</p>
    </header>
    <section>
      <h2>Participant direction</h2>
      <p>{safe_instruction}</p>
    </section>
    <section>
      <h2>Selected context</h2>
      <p>{safe_context}</p>
    </section>
    <section>
      <h2>Featured work</h2>
      <ul>
        <li>Insight dashboard for collaborative research teams.</li>
        <li>Accessible onboarding flow for a creative portfolio platform.</li>
        <li>Design system refresh focused on contrast, spacing, and clarity.</li>
      </ul>
    </section>
    <section>
      <h2>Skills</h2>
      <span class="tag">Product strategy</span>
      <span class="tag">UX research</span>
      <span class="tag">Interface design</span>
      <span class="tag">Prototyping</span>
    </section>
    <section>
      <h2>Contact</h2>
      <p>Email Alex at hello@example.com to discuss thoughtful product design.</p>
    </section>
  </main>
</body>
</html>
""".strip()
    response_payload = {
        "id": "fallback-deterministic",
        "object": "chat.completion",
        "choices": [{"message": {"role": "assistant", "content": generated}}],
    }
    normalized = normalize_website_html(generated)
    return {
        "backend": "fallback_bot_response",
        "fallback_reason": fallback_reason,
        "ai_request_payload": request_payload,
        "ai_request_config": request_config,
        "model_availability": availability,
        "ai_response_payload": response_payload,
        "raw_ai_response": generated,
        "generated_website": normalized["html"],
        "normalization": normalized,
        "elapsed_seconds": 0.0,
    }


def instruction_for_bot(position: int) -> str:
    if position == 1:
        return "Create a calm, modern portfolio with a strong hero and three case studies."
    if position == 2:
        return "Improve the portfolio by adding clearer project outcomes and warmer colors."
    return "Keep the clearer project outcomes and improve the contact section."


def validate_instruction(answer, **kwargs):
    if not answer or len(answer.strip()) < 10:
        return "Please write at least one specific sentence for the AI."
    return None


class InstructionPage(ModularPage):
    def __init__(self, label: str, prompt: Markup, time_estimate: float, bot_response):
        super().__init__(
            label,
            prompt,
            control=TextControl(
                one_line=False,
                width="100%",
                height="140px",
                bot_response=bot_response,
            ),
            time_estimate=time_estimate,
            validate=validate_instruction,
        )

    def format_answer(self, raw_answer, **kwargs):
        return (raw_answer or "").strip()


class PortfolioNetwork(ImitationChainNetwork):
    def make_definition(self):
        return {"portfolio_task": PORTFOLIO_TASK}


class PortfolioTrial(ImitationChainTrial):
    time_estimate = 45
    accumulate_answers = True
    check_time_credit_received = False

    def previous_definition(self):
        return self.definition

    def two_rounds_earlier_definition(self):
        return get_parent_definition(self.node)

    def show_trial(self, experiment, participant):
        position = self.node.degree + 1
        pages = [
            InfoPage(
                Markup(
                    "<h2>Portfolio website chain</h2>"
                    "<p>You are contributing one instruction to a collaborative "
                    "chain. You are not writing website code directly; your role "
                    "is to tell the AI what portfolio website to create or improve.</p>"
                ),
                time_estimate=5,
            )
        ]

        if position == 1:
            pages.append(
                InstructionPage(
                    "instruction",
                    Markup(
                        "<h3>Create the first website version</h3>"
                        f"<p><strong>Original task:</strong> {html.escape(PORTFOLIO_TASK)}</p>"
                        "<p>Write one instruction for the AI that will produce the "
                        "first portfolio website.</p>"
                    ),
                    time_estimate=35,
                    bot_response=lambda bot: instruction_for_bot(position),
                )
            )
            return join(*pages)

        previous_html = get_previous_website(self.previous_definition())
        pages.append(
            InfoPage(
                Markup(
                    "<h3>Original task and previous website</h3>"
                    f"<p><strong>Original task:</strong> {html.escape(PORTFOLIO_TASK)}</p>"
                    f"{website_iframe(previous_html, 'Website from the previous round')}"
                ),
                time_estimate=10,
            )
        )

        if position == 2:
            pages.append(
                InstructionPage(
                    "instruction",
                    Markup(
                        "<h3>Improve the previous website</h3>"
                        "<p>Do you have suggestions to improve this website? Write "
                        "one concrete instruction for the AI.</p>"
                    ),
                    time_estimate=30,
                    bot_response=lambda bot: instruction_for_bot(position),
                )
            )
            return join(*pages)

        earlier_definition = self.two_rounds_earlier_definition()
        earlier_html = get_previous_website(earlier_definition or {})
        pages.append(
            ModularPage(
                "comparison_choice",
                Markup(
                    "<h3>Choose which recent website is better</h3>"
                    "<p>Your choice determines which recent website version is "
                    "carried forward for the AI to improve.</p>"
                    f"{website_pair(previous_html, earlier_html)}"
                ),
                control=RadioButtonControl(
                    ["previous", "two_rounds_earlier"],
                    ["Website A: previous round", "Website B: two rounds earlier"],
                ),
                time_estimate=20,
                bot_response=lambda bot: "previous",
            )
        )
        pages.append(
            PageMaker(
                lambda participant: self.make_selected_instruction_page(
                    (participant.answer or {}).get("comparison_choice", "previous")
                ),
                time_estimate=30,
            )
        )
        return join(*pages)

    def make_selected_instruction_page(self, selected: str):
        selected_html = self.get_selected_context(selected)["website_html"]
        label = (
            "Website A: previous round"
            if selected == "previous"
            else "Website B: two rounds earlier"
        )
        return InstructionPage(
            "instruction",
            Markup(
                "<h3>Improve the selected website</h3>"
                f"<p><strong>Original task:</strong> {html.escape(PORTFOLIO_TASK)}</p>"
                f"{website_iframe(selected_html, label)}"
                "<p>Write one instruction for the AI to improve the selected website.</p>"
            ),
            time_estimate=30,
            bot_response=lambda bot: instruction_for_bot(self.node.degree + 1),
        )

    def get_selected_context(self, selected: Optional[str]) -> Dict[str, Any]:
        previous_definition = self.previous_definition()
        earlier_definition = self.two_rounds_earlier_definition()
        if selected == "two_rounds_earlier" and earlier_definition:
            return {
                "selected_comparison_winner": "two_rounds_earlier",
                "selected_node_id": self.node.parent.id if self.node.parent else None,
                "website_html": earlier_definition.get("generated_website", ""),
            }
        return {
            "selected_comparison_winner": "previous",
            "selected_node_id": self.node.id,
            "website_html": previous_definition.get("generated_website", ""),
        }

    def format_answer(self, raw_answer, **kwargs):
        answer = raw_answer or {}
        position = self.node.degree + 1
        participant_instruction = (answer.get("instruction") or "").strip()
        selected = answer.get("comparison_choice")

        if position == 1:
            website_context = PORTFOLIO_TASK
            selected_context = {
                "selected_comparison_winner": None,
                "selected_node_id": None,
                "website_html": None,
            }
        elif position == 2:
            website_context = self.definition.get("generated_website", "")
            selected_context = {
                "selected_comparison_winner": "previous",
                "selected_node_id": self.node.id,
                "website_html": website_context,
            }
        else:
            selected_context = self.get_selected_context(selected)
            website_context = selected_context["website_html"]

        ai_result = call_openrouter(participant_instruction, website_context)
        parent_ids = [
            node_id
            for node_id in [
                self.node.parent.id if self.node.parent else None,
                self.node.id,
            ]
            if node_id is not None
        ]
        previous_history = self.definition.get("history", [])
        contribution = {
            "node_position": position,
            "source_node_id": self.node.id,
            "parent_node_ids": parent_ids,
            "original_task_instruction": PORTFOLIO_TASK,
            "participant_instruction": participant_instruction,
            "selected_comparison_winner": selected_context[
                "selected_comparison_winner"
            ],
            "selected_node_id": selected_context["selected_node_id"],
            "website_context": website_context,
            "backend": ai_result["backend"],
            "fallback_reason": ai_result["fallback_reason"],
            "ai_request_payload": ai_result["ai_request_payload"],
            "ai_request_config": ai_result["ai_request_config"],
            "model_availability": ai_result["model_availability"],
            "ai_response_payload": ai_result["ai_response_payload"],
            "raw_ai_response": ai_result["raw_ai_response"],
            "generated_website": ai_result["generated_website"],
            "normalization": ai_result["normalization"],
            "created_at": utc_now(),
            "elapsed_seconds": ai_result["elapsed_seconds"],
        }
        return {
            **contribution,
            "node_id": None,
            "previous_definition_node_id": self.definition.get("node_id"),
            "history": previous_history + [contribution],
        }


class PortfolioNode(ImitationChainNode):
    def create_initial_seed(self, experiment, participant):
        return {
            "node_id": None,
            "node_position": 0,
            "original_task_instruction": PORTFOLIO_TASK,
            "generated_website": None,
            "history": [],
            "created_at": utc_now(),
        }

    def create_definition_from_seed(self, seed, experiment, participant):
        definition = dict(seed)
        definition["node_id"] = self.id
        return definition

    def summarize_trials(self, trials: list, experiment, participant):
        if len(trials) > 1:
            for trial in trials[1:]:
                trial.fail(reason="Too many trials at the same chain node")
        return trials[0].answer


class PortfolioTrialMaker(ImitationChainTrialMaker):
    response_timeout_sec = 90
    check_timeout_interval_sec = 30


class Exp(psynet.experiment.Experiment):
    label = "Portfolio website chain"
    initial_recruitment_size = 1
    test_n_bots = 3

    timeline = Timeline(
        InfoPage(
            Markup(
                "<h1>Portfolio website chain</h1>"
                "<p>In this study, each participant writes one instruction for "
                "an AI model that creates or improves a portfolio website.</p>"
            ),
            time_estimate=5,
        ),
        PortfolioTrialMaker(
            id_="portfolio_website_chain",
            network_class=PortfolioNetwork,
            trial_class=PortfolioTrial,
            node_class=PortfolioNode,
            chain_type="across",
            max_nodes_per_chain=4,
            max_trials_per_participant=1,
            expected_trials_per_participant=1,
            chains_per_participant=None,
            chains_per_experiment=1,
            trials_per_node=1,
            balance_across_chains=True,
            check_performance_at_end=False,
            check_performance_every_trial=False,
            recruit_mode="n_participants",
            target_n_participants=3,
        ),
        InfoPage("You finished the experiment. Thank you!", time_estimate=0),
    )

    def test_check_bot(self, bot: Bot, **kwargs):
        assert len(bot.alive_trials) == 1
        trial = bot.alive_trials[0]
        assert trial.answer["participant_instruction"]
        assert trial.answer["ai_request_payload"]["messages"]
        assert trial.answer["backend"] in {"openrouter", "fallback_bot_response"}
        assert trial.answer["generated_website"].lower().startswith("<!doctype html>")
        assert trial.answer["ai_request_config"]["api_key_present"] is False

    def test_check_bots(self, bots: List[Bot], **kwargs):
        trials = sorted(
            [bot.alive_trials[0] for bot in bots],
            key=lambda trial: trial.answer["node_position"],
        )
        positions = [trial.answer["node_position"] for trial in trials]
        assert positions == [1, 2, 3]
        assert trials[2].answer["selected_comparison_winner"] == "previous"
        assert all(
            trial.answer["backend"] == "fallback_bot_response" for trial in trials
        )
