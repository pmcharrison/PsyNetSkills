import datetime as dt
import json
import os
import re
import urllib.error
import urllib.request
from html import escape as html_escape

import psynet.experiment
from markupsafe import Markup, escape
from psynet.modular_page import ModularPage, RadioButtonControl, TextControl
from psynet.page import InfoPage
from psynet.timeline import FailedValidation, Timeline, join
from psynet.trial.chain import ChainNode, ChainTrial, ChainTrialMaker
from psynet.utils import get_from_config


ORIGINAL_TASK = (
    "Create a concise portfolio website for a fictional creative technologist. "
    "The site should include a hero section, a short biography, selected "
    "projects, skills, and contact details."
)

DEFAULT_MODEL = "openai/gpt-4o-mini"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_TIMEOUT_SECONDS = 20


class NonEmptyInstructionControl(TextControl):
    def validate(self, response, **kwargs):
        if not str(response.answer or "").strip():
            return FailedValidation("Please write an instruction for the AI.")
        return None


class BotRadioButtonControl(RadioButtonControl):
    def __init__(self, *args, bot_response_choice=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot_response_choice = bot_response_choice

    def get_bot_response(self, experiment, bot, page, prompt):
        return self.bot_response_choice or self.choices[0]


def now_iso():
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def read_setting(config_key, env_key, default=None):
    value = os.environ.get(env_key)
    if value:
        return value
    try:
        value = get_from_config(config_key)
    except Exception:
        value = None
    return value if value not in (None, "") else default


def openrouter_settings():
    timeout = read_setting(
        "openrouter_timeout_seconds",
        "OPENROUTER_TIMEOUT_SECONDS",
        DEFAULT_TIMEOUT_SECONDS,
    )
    try:
        timeout = float(timeout)
    except (TypeError, ValueError):
        timeout = DEFAULT_TIMEOUT_SECONDS
    return {
        "api_key": read_setting("openrouter_api_key", "OPENROUTER_API_KEY"),
        "model": read_setting("openrouter_model", "OPENROUTER_MODEL", DEFAULT_MODEL),
        "base_url": str(
            read_setting("openrouter_base_url", "OPENROUTER_BASE_URL", DEFAULT_BASE_URL)
        ).rstrip("/"),
        "timeout": timeout,
    }


def url_json_request(url, payload=None, api_key=None, timeout=DEFAULT_TIMEOUT_SECONDS):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def check_model_available(settings):
    if not settings["api_key"]:
        return False, "OPENROUTER_API_KEY/openrouter_api_key is not configured."
    try:
        payload = url_json_request(
            f"{settings['base_url']}/models",
            api_key=settings["api_key"],
            timeout=settings["timeout"],
        )
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
        return False, f"Could not check OpenRouter model availability: {e}"
    model_ids = {item.get("id") for item in payload.get("data", []) if item.get("id")}
    if settings["model"] not in model_ids:
        return False, f"Configured OpenRouter model is unavailable: {settings['model']}"
    return True, None


def build_messages(participant_instruction, context_label, website_context):
    return [
        {
            "role": "system",
            "content": (
                "You are helping participants iteratively create a portfolio website. "
                "Return only a complete, self-contained HTML document. Do not include "
                "JavaScript, remote scripts, tracking pixels, or external credentials."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Original task:\n{ORIGINAL_TASK}\n\n"
                f"Context ({context_label}):\n{website_context}\n\n"
                f"Participant instruction:\n{participant_instruction}\n\n"
                "Create the next portfolio website version as HTML."
            ),
        },
    ]


def make_request_payload(participant_instruction, context_label, website_context, model):
    return {
        "model": model,
        "messages": build_messages(participant_instruction, context_label, website_context),
        "temperature": 0.2,
        "max_tokens": 2500,
    }


def extract_message_content(response_payload):
    return response_payload["choices"][0]["message"]["content"]


def fallback_response(participant_instruction, context_label, website_context, reason):
    escaped_instruction = html_escape(participant_instruction)
    escaped_context = html_escape(context_label)
    escaped_preview = html_escape(str(website_context)[:600])
    generated = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Portfolio Website Draft</title>
  <style>
    body {{ margin: 0; font-family: Inter, Arial, sans-serif; color: #172033; background: #f7f8fb; }}
    header {{ padding: 48px; background: linear-gradient(135deg, #263a72, #8468d8); color: white; }}
    main {{ max-width: 900px; margin: 0 auto; padding: 32px; }}
    section {{ background: white; border-radius: 18px; padding: 24px; margin: 18px 0; box-shadow: 0 12px 30px #17203318; }}
    .tag {{ display: inline-block; padding: 6px 10px; border-radius: 999px; background: #e7edff; margin: 4px; }}
  </style>
</head>
<body>
  <header>
    <p>AI-assisted portfolio draft</p>
    <h1>Jordan Vale, Creative Technologist</h1>
    <p>{escaped_instruction}</p>
  </header>
  <main>
    <section><h2>About</h2><p>Jordan blends interactive design, front-end engineering, and accessible storytelling.</p></section>
    <section><h2>Selected projects</h2><ul><li>Immersive museum guide</li><li>Generative identity system</li><li>Climate data microsite</li></ul></section>
    <section><h2>Skills</h2><span class="tag">UX</span><span class="tag">HTML/CSS</span><span class="tag">Data stories</span></section>
    <section><h2>Context carried forward</h2><p><strong>{escaped_context}</strong></p><pre>{escaped_preview}</pre></section>
    <section><h2>Contact</h2><p>jordan.vale@example.test</p></section>
  </main>
</body>
</html>"""
    return {
        "backend": "fallback",
        "fallback_reason": reason,
        "response_payload": {
            "backend": "bot_response",
            "reason": reason,
            "content": generated,
        },
        "raw_content": generated,
    }


def generate_website(participant_instruction, context_label, website_context):
    settings = openrouter_settings()
    request_payload = make_request_payload(
        participant_instruction, context_label, website_context, settings["model"]
    )
    available, fallback_reason = check_model_available(settings)
    if not available:
        result = fallback_response(
            participant_instruction, context_label, website_context, fallback_reason
        )
        result["request_payload"] = request_payload
        return result
    try:
        response_payload = url_json_request(
            f"{settings['base_url']}/chat/completions",
            payload=request_payload,
            api_key=settings["api_key"],
            timeout=settings["timeout"],
        )
        return {
            "backend": "openrouter",
            "fallback_reason": None,
            "request_payload": request_payload,
            "response_payload": response_payload,
            "raw_content": extract_message_content(response_payload),
        }
    except (
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        TimeoutError,
        urllib.error.URLError,
        urllib.error.HTTPError,
    ) as e:
        result = fallback_response(
            participant_instruction,
            context_label,
            website_context,
            f"OpenRouter completion failed: {e}",
        )
        result["request_payload"] = request_payload
        return result


def sanitize_website(raw_content):
    content = str(raw_content or "").strip()
    if not content:
        return (
            "<!doctype html><html><body><h1>Empty AI response</h1>"
            "<p>No website content was returned.</p></body></html>",
            {"empty": True, "removed_script": False, "removed_event_handlers": False},
        )
    removed_script = bool(re.search(r"<\s*script", content, flags=re.I))
    removed_handlers = bool(re.search(r"\son[a-z]+\s*=", content, flags=re.I))
    content = re.sub(r"<\s*script\b[^>]*>.*?<\s*/\s*script\s*>", "", content, flags=re.I | re.S)
    content = re.sub(r"\son[a-z]+\s*=\s*(['\"]).*?\1", "", content, flags=re.I | re.S)
    content = re.sub(r"\son[a-z]+\s*=\s*[^\s>]+", "", content, flags=re.I)
    content = re.sub(r"javascript\s*:", "", content, flags=re.I)
    content = re.sub(
        r"<\s*meta\b[^>]*http-equiv\s*=\s*(['\"]?)refresh\1[^>]*>",
        "",
        content,
        flags=re.I,
    )
    if "<html" not in content.lower():
        content = f"<!doctype html><html><body>{content}</body></html>"
    return content, {
        "empty": False,
        "removed_script": removed_script,
        "removed_event_handlers": removed_handlers,
    }


def website_frame(title, website):
    return Markup(
        f"""
        <section style="margin: 1rem 0;">
          <h3>{escape(title)}</h3>
          <iframe
            title="{escape(title)}"
            sandbox=""
            srcdoc="{escape(website)}"
            style="width: 100%; min-height: 420px; border: 1px solid #cfd6e6; border-radius: 12px; background: white;"
          ></iframe>
        </section>
        """
    )


def instruction_bot_response(bot=None, **kwargs):
    bot_id = getattr(bot, "id", "bot")
    return (
        f"Bot {bot_id}: make the portfolio more polished, accessible, and specific. "
        "Use clear project cards, concise text, and a strong call to action."
    )


def extract_answer_value(answer, key, default=None):
    if isinstance(answer, dict):
        return answer.get(key, default)
    if key == "participant_instruction" and isinstance(answer, str):
        return answer
    return default


def selected_context_for_node(degree, node_id, definition, parent, selected_winner):
    if degree == 0:
        return "original portfolio task", ORIGINAL_TASK, None
    if degree < 2 or selected_winner in (None, "previous"):
        return "previous website", definition["generated_website"], node_id
    if selected_winner == "two_rounds_earlier" and parent:
        return (
            "website from two rounds earlier",
            parent.definition["generated_website"],
            parent.id,
        )
    return "previous website", definition["generated_website"], node_id


def build_next_definition(degree, node_id, definition, parent, answer):
    participant_instruction = str(
        extract_answer_value(answer, "participant_instruction", "")
    ).strip()
    selected_winner = extract_answer_value(answer, "selected_comparison_winner")
    context_label, context_website, context_source_node_id = selected_context_for_node(
        degree, node_id, definition, parent, selected_winner
    )
    ai_result = generate_website(participant_instruction, context_label, context_website)
    generated_website, sanitization = sanitize_website(ai_result["raw_content"])
    parent_ids = list(definition.get("parent_node_ids", [])) + [node_id]
    history = list(definition.get("chain_history", []))
    record = {
        "source_node_id": node_id,
        "new_node_position": degree + 1,
        "participant_instruction": participant_instruction,
        "selected_comparison_winner": selected_winner,
        "context_source_node_id": context_source_node_id,
        "ai_backend": ai_result["backend"],
        "fallback_reason": ai_result["fallback_reason"],
        "created_at": now_iso(),
    }
    history.append(record)
    return {
        "node_position": degree + 1,
        "parent_node_ids": parent_ids,
        "source_parent_node_id": node_id,
        "original_task_instruction": ORIGINAL_TASK,
        "participant_instruction": participant_instruction,
        "has_suggestions": extract_answer_value(answer, "has_suggestions"),
        "selected_comparison_winner": selected_winner,
        "website_context_label": context_label,
        "website_context_source_node_id": context_source_node_id,
        "website_context": context_website,
        "ai_backend": ai_result["backend"],
        "fallback_reason": ai_result["fallback_reason"],
        "ai_request_payload": ai_result["request_payload"],
        "ai_response_payload": ai_result["response_payload"],
        "raw_ai_response": ai_result["raw_content"],
        "generated_website": generated_website,
        "sanitization": sanitization,
        "created_at": now_iso(),
        "chain_history": history,
    }


class PortfolioNode(ChainNode):
    def make_next_definition(self, experiment, participant):
        trial = self.completed_and_processed_trials[0]
        return build_next_definition(
            self.degree, self.id, self.definition, self.parent, trial.answer or {}
        )


def start_nodes():
    return [
        PortfolioNode(
            definition={
                "node_position": 0,
                "parent_node_ids": [],
                "source_parent_node_id": None,
                "original_task_instruction": ORIGINAL_TASK,
                "generated_website": None,
                "chain_history": [],
                "created_at": now_iso(),
            }
        )
    ]


class PortfolioTrial(ChainTrial):
    time_estimate = 90
    accumulate_answers = True
    check_time_credit_received = False

    def show_trial(self, experiment, participant):
        pages = [self.introduction_page()]
        if self.degree == 0:
            pages.append(self.instruction_page("Create the first website version."))
        elif self.degree == 1:
            pages.extend(
                [
                    self.previous_website_page(),
                    self.suggestions_page(),
                    self.instruction_page("Tell the AI how to improve this website."),
                ]
            )
        else:
            pages.extend(
                [
                    self.comparison_page(),
                    self.instruction_page(
                        "Tell the AI how to improve the website you selected."
                    ),
                ]
            )
        return join(*pages)

    def introduction_page(self):
        if self.degree == 0:
            body = (
                "<h2>Create a portfolio website with AI assistance</h2>"
                f"<p>{escape(ORIGINAL_TASK)}</p>"
                "<p>You are not writing website code directly. Write a clear instruction "
                "for the AI describing the first version it should create.</p>"
            )
        elif self.degree == 1:
            body = (
                "<h2>Improve the previous portfolio website</h2>"
                f"<p>Original task: {escape(ORIGINAL_TASK)}</p>"
                "<p>Review the previous participant's website, decide whether you have "
                "suggestions, then write an instruction for the AI.</p>"
            )
        else:
            body = (
                "<h2>Compare recent portfolio websites</h2>"
                "<p>Choose which recent website is better. Your choice determines which "
                "version is carried forward for the next AI revision.</p>"
            )
        return InfoPage(Markup(body), time_estimate=10)

    def previous_website_page(self):
        return InfoPage(
            website_frame("Website from the previous round", self.definition["generated_website"]),
            time_estimate=20,
        )

    def comparison_page(self):
        prompt = Markup(
            "<p>First inspect both recent websites, then choose which one should be "
            "carried forward.</p>"
        )
        return join(
            InfoPage(
                join_markup(
                    website_frame(
                        "Previous round",
                        self.definition["generated_website"],
                    ),
                    website_frame(
                        "Two rounds earlier",
                        self.node.parent.definition["generated_website"],
                    ),
                ),
                time_estimate=25,
            ),
            ModularPage(
                "selected_comparison_winner",
                prompt,
                BotRadioButtonControl(
                    ["previous", "two_rounds_earlier"],
                    ["Previous round", "Two rounds earlier"],
                    name="comparison_winner",
                    bot_response_choice="previous",
                ),
                time_estimate=10,
            ),
        )

    def suggestions_page(self):
        return ModularPage(
            "has_suggestions",
            "Do you have suggestions that could improve the previous website?",
            BotRadioButtonControl(
                ["yes", "no"],
                ["Yes", "No, but I can still suggest a direction"],
                name="has_suggestions",
                bot_response_choice="yes",
            ),
            time_estimate=10,
        )

    def instruction_page(self, prompt):
        return ModularPage(
            "participant_instruction",
            prompt,
            NonEmptyInstructionControl(
                one_line=False,
                width="100%",
                height="180px",
                bot_response=instruction_bot_response,
            ),
            time_estimate=50,
        )


def join_markup(*parts):
    return Markup("".join(str(part) for part in parts))


class Exp(psynet.experiment.Experiment):
    label = "Portfolio website chain"
    timeline = Timeline(
        ChainTrialMaker(
            id_="portfolio_website_chain",
            trial_class=PortfolioTrial,
            node_class=PortfolioNode,
            chain_type="across",
            start_nodes=start_nodes,
            expected_trials_per_participant=1,
            max_trials_per_participant=1,
            max_nodes_per_chain=4,
            trials_per_node=1,
            recruit_mode="n_trials",
        )
    )
    test_n_bots = 1
    test_mode = "serial"
    test_time_factor = 0.1

    def test_check_bot(self, bot, **kwargs):
        super().test_check_bot(bot, **kwargs)
        for trial in bot.alive_trials:
            assert "participant_instruction" in trial.answer
            if trial.degree >= 2:
                assert trial.answer["selected_comparison_winner"] == "previous"

    def test_check_bots(self, bots, **kwargs):
        super().test_check_bots(bots, **kwargs)
        trials = PortfolioTrial.query.order_by(PortfolioTrial.id).all()
        assert len(trials) == 1
        assert "participant_instruction" in trials[0].answer
        generated_definitions = [
            node.definition
            for node in PortfolioNode.query.all()
            if node.definition.get("generated_website")
        ]
        assert generated_definitions, "Expected generated website nodes in the chain."
        last_definition = generated_definitions[-1]
        required_keys = {
            "participant_instruction",
            "website_context",
            "ai_backend",
            "fallback_reason",
            "ai_request_payload",
            "ai_response_payload",
            "generated_website",
            "chain_history",
        }
        assert required_keys.issubset(last_definition)
        assert last_definition["ai_backend"] == "fallback"
        assert last_definition["fallback_reason"]
        assert len(last_definition["chain_history"]) >= 1
