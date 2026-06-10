"""Portfolio website chain experiment with AI editing and fallback bots."""

import json
import os
import re
import urllib.error
import urllib.request
from copy import deepcopy
from datetime import datetime, timezone

from dominate import tags
from markupsafe import Markup

import psynet.experiment
from psynet.modular_page import (
    ModularPage,
    RadioButtonControl,
    TextControl,
)
from psynet.page import InfoPage
from psynet.timeline import Timeline, join
from psynet.trial.chain import ChainNode, ChainTrial, ChainTrialMaker
from psynet.utils import get_logger

logger = get_logger()

PORTFOLIO_TASK = (
    "Create a polished personal portfolio website for a fictional creative "
    "professional. The site should introduce the person, summarize selected "
    "projects, include contact information, and look coherent as a standalone "
    "single-page website."
)

DEFAULT_HTML = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Portfolio draft</title>
    <style>
      body { font-family: Inter, Arial, sans-serif; margin: 2rem; color: #1f2937; }
      main { max-width: 760px; margin: auto; }
      header { border-bottom: 3px solid #2563eb; margin-bottom: 1.5rem; }
      h1 { color: #111827; }
      section { margin: 1.5rem 0; }
      .project { padding: 1rem; border: 1px solid #d1d5db; border-radius: 12px; }
    </style>
  </head>
  <body>
    <main>
      <header>
        <h1>Avery Morgan</h1>
        <p>Designer and front-end developer building warm digital experiences.</p>
      </header>
      <section>
        <h2>Featured work</h2>
        <div class="project">Brand refresh, interactive gallery, and nonprofit launch page.</div>
      </section>
      <section>
        <h2>Contact</h2>
        <p>Email: avery@example.com</p>
      </section>
    </main>
  </body>
</html>"""


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_html(html):
    """Conservatively remove active content before iframe display."""
    html = html or ""
    html = re.sub(r"<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>", "", html, flags=re.I)
    html = re.sub(r"\son[a-z]+\s*=\s*(['\"]).*?\1", "", html, flags=re.I | re.S)
    html = re.sub(r"javascript:", "", html, flags=re.I)
    if "<html" not in html.lower():
        html = f"<!doctype html><html><body>{html}</body></html>"
    return html


def website_frame(title, html):
    return tags.div(
        tags.h4(title),
        tags.iframe(
            srcdoc=clean_html(html),
            sandbox="",
            style=(
                "width: 100%; height: 360px; border: 1px solid #cbd5e1; "
                "border-radius: 8px; background: white;"
            ),
        ),
        style="margin: 1rem 0;",
    )


def bot_response(instruction, context_html, position):
    context_note = "first draft" if position == 1 else "revision"
    accent = ["#2563eb", "#7c3aed", "#059669", "#dc2626"][position % 4]
    instruction = instruction.strip() or "Make a clear, professional portfolio page."
    return f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Fallback portfolio {position}</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }}
      main {{ max-width: 860px; margin: 0 auto; padding: 2rem; }}
      header {{ background: {accent}; color: white; padding: 2rem; border-radius: 18px; }}
      section {{ background: white; margin: 1rem 0; padding: 1.25rem; border-radius: 14px; }}
      .badge {{ display: inline-block; padding: .25rem .6rem; background: #e0f2fe; border-radius: 999px; }}
    </style>
  </head>
  <body>
    <main>
      <header>
        <p class="badge">Deterministic {context_note}</p>
        <h1>Avery Morgan Portfolio</h1>
        <p>{instruction}</p>
      </header>
      <section>
        <h2>Selected projects</h2>
        <p>Interactive identity systems, editorial websites, and accessible product pages.</p>
      </section>
      <section>
        <h2>Iteration context</h2>
        <p>This version was generated from {len(context_html)} characters of prior website context.</p>
      </section>
      <section>
        <h2>Contact</h2>
        <p>avery@example.com</p>
      </section>
    </main>
  </body>
</html>"""


def api_settings():
    return {
        "api_key": os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"),
        "model": os.getenv("OPENROUTER_MODEL") or os.getenv("OPENAI_MODEL"),
        "base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        "timeout": float(os.getenv("OPENROUTER_TIMEOUT", "20")),
    }


def model_is_available(settings):
    if not settings["api_key"]:
        return False, "missing_api_key"
    if not settings["model"]:
        return False, "missing_model"

    request = urllib.request.Request(
        f"{settings['base_url'].rstrip('/')}/models",
        headers={"Authorization": f"Bearer {settings['api_key']}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=settings["timeout"]) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("Model availability check failed: %s", exc)
        return False, "model_check_failed"

    models = payload.get("data", [])
    available = any(model.get("id") == settings["model"] for model in models)
    return (True, None) if available else (False, "model_unavailable")


def build_ai_request(instruction, context_html):
    return {
        "model": api_settings()["model"],
        "messages": [
            {
                "role": "system",
                "content": (
                    "You create safe standalone single-page portfolio websites. "
                    "Return only complete HTML. Do not include scripts, external "
                    "tracking, or secrets."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Original task:\n{PORTFOLIO_TASK}\n\n"
                    f"Current or selected website context:\n{context_html}\n\n"
                    f"Participant instruction:\n{instruction}\n\n"
                    "Return a complete improved HTML document."
                ),
            },
        ],
        "temperature": 0.7,
    }


def call_ai_or_fallback(instruction, context_html, position):
    settings = api_settings()
    request_payload = build_ai_request(instruction, context_html)
    available, fallback_reason = model_is_available(settings)
    if not available:
        raw_html = bot_response(instruction, context_html, position)
        return {
            "backend": "fallback_bot_response",
            "fallback_reason": fallback_reason,
            "ai_request": request_payload,
            "ai_response": {"content": raw_html},
            "raw_website_html": raw_html,
            "website_html": clean_html(raw_html),
        }

    request = urllib.request.Request(
        f"{settings['base_url'].rstrip('/')}/chat/completions",
        data=json.dumps(request_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings['api_key']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=settings["timeout"]) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
        raw_html = response_payload["choices"][0]["message"]["content"]
        backend = "openrouter"
        fallback_reason = None
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError) as exc:
        logger.warning("AI call failed; falling back to bot_response: %s", exc)
        fallback_reason = "ai_call_failed"
        raw_html = bot_response(instruction, context_html, position)
        response_payload = {"content": raw_html, "error": str(exc)}
        backend = "fallback_bot_response"

    return {
        "backend": backend,
        "fallback_reason": fallback_reason,
        "ai_request": request_payload,
        "ai_response": response_payload,
        "raw_website_html": raw_html,
        "website_html": clean_html(raw_html),
    }


class PortfolioChainNode(ChainNode):
    def make_next_definition(self, experiment, participant):
        return deepcopy(self.completed_and_processed_trials[0].answer["next_definition"])

    def summarize_trials(self, trials, experiment, participant):
        return trials[0].answer


def get_start_nodes():
    return [
        PortfolioChainNode(
            definition={
                "position": 1,
                "original_task": PORTFOLIO_TASK,
                "history": [],
                "previous_website": None,
                "two_back_website": None,
            }
        )
    ]


class PortfolioTrial(ChainTrial):
    time_estimate = 90
    accumulate_answers = True
    check_time_credit_received = False

    def show_trial(self, experiment, participant):
        position = self.definition["position"]
        pages = []
        if position == 1:
            pages.append(
                InfoPage(
                    Markup(
                        "<h2>Create the first portfolio website</h2>"
                        f"<p>{PORTFOLIO_TASK}</p>"
                        "<p>You will write an instruction for an AI assistant. "
                        "The AI will use your instruction to create the first "
                        "version of the website.</p>"
                    ),
                    time_estimate=10,
                )
            )
        elif position == 2:
            pages.append(
                InfoPage(
                    tags.div(
                        tags.h2("Improve the previous website"),
                        tags.p(PORTFOLIO_TASK),
                        tags.p(
                            "Review the website from the previous round. If you "
                            "have suggestions, write them as an instruction for "
                            "the AI on the next page."
                        ),
                        website_frame(
                            "Previous website",
                            self.definition["previous_website"]["website_html"],
                        ),
                    ),
                    time_estimate=20,
                )
            )
        else:
            pages.extend(
                [
                    InfoPage(
                        tags.div(
                            tags.h2("Compare the two recent websites"),
                            tags.p(
                                "First compare the website from the previous "
                                "round with the website from two rounds ago."
                            ),
                            website_frame(
                                "Website A: previous round",
                                self.definition["previous_website"]["website_html"],
                            ),
                            website_frame(
                                "Website B: two rounds ago",
                                self.definition["two_back_website"]["website_html"],
                            ),
                        ),
                        time_estimate=25,
                    ),
                    ModularPage(
                        "comparison_choice",
                        "Which website is better?",
                        RadioButtonControl(
                            choices=["previous", "two_back"],
                            labels=[
                                "Website A: previous round",
                                "Website B: two rounds ago",
                            ],
                        ),
                        time_estimate=10,
                    ),
                ]
            )

        pages.append(
            ModularPage(
                "instruction",
                "Write a clear instruction for the AI portfolio website editor.",
                TextControl(
                    block_copy_paste=False,
                    bot_response=lambda: (
                        "Improve the layout, add stronger project descriptions, "
                        "and make the contact section more inviting."
                    ),
                ),
                time_estimate=30,
            )
        )
        return join(*pages)

    def format_answer(self, raw_answer, **kwargs):
        if isinstance(raw_answer, dict):
            instruction = raw_answer.get("instruction", "")
            comparison_choice = raw_answer.get("comparison_choice")
        else:
            instruction = raw_answer
            comparison_choice = None

        position = self.definition["position"]
        selected_context = self._selected_context(comparison_choice)
        generated = call_ai_or_fallback(instruction, selected_context, position)
        history_entry = {
            "node_position": position,
            "node_id": self.node.id,
            "parent_node_id": self.node.parent_id,
            "original_task": PORTFOLIO_TASK,
            "participant_instruction": instruction,
            "comparison_choice": comparison_choice,
            "selected_context": selected_context,
            "backend": generated["backend"],
            "fallback_reason": generated["fallback_reason"],
            "ai_request": generated["ai_request"],
            "ai_response": generated["ai_response"],
            "raw_website_html": generated["raw_website_html"],
            "website_html": generated["website_html"],
            "created_at": now_iso(),
        }
        history = [*self.definition["history"], history_entry]
        return {
            **history_entry,
            "next_definition": {
                "position": position + 1,
                "original_task": PORTFOLIO_TASK,
                "history": history,
                "previous_website": history[-1],
                "two_back_website": history[-2] if len(history) >= 2 else None,
            },
        }

    def _selected_context(self, comparison_choice):
        position = self.definition["position"]
        if position == 1:
            return DEFAULT_HTML
        if position == 2 or comparison_choice == "previous":
            return self.definition["previous_website"]["website_html"]
        if comparison_choice == "two_back":
            return self.definition["two_back_website"]["website_html"]
        return self.definition["previous_website"]["website_html"]


def get_timeline():
    return Timeline(
        ChainTrialMaker(
            id_="portfolio_websites",
            trial_class=PortfolioTrial,
            node_class=PortfolioChainNode,
            chain_type="across",
            start_nodes=get_start_nodes,
            expected_trials_per_participant=1,
            max_nodes_per_chain=4,
            max_trials_per_participant=1,
            chains_per_experiment=1,
            trials_per_node=1,
            recruit_mode="n_trials",
            wait_for_networks=True,
            check_performance_at_end=False,
            check_performance_every_trial=False,
        ),
        InfoPage(
            "Thank you. Your instruction has been saved and the next website "
            "version has been generated.",
            time_estimate=0,
        ),
    )


class Exp(psynet.experiment.Experiment):
    label = "Portfolio website chain"
    config = {
        "show_reward": False,
    }
    timeline = get_timeline()
    test_n_bots = 4

    def test_check_bots(self, bots):
        super().test_check_bots(bots)
        complete_trials = (
            PortfolioTrial.query.filter_by(complete=True)
            .order_by(PortfolioTrial.id)
            .all()
        )
        assert len(complete_trials) >= 3
        answers = [trial.answer for trial in complete_trials]
        assert answers[0]["node_position"] == 1
        assert answers[1]["node_position"] == 2
        assert answers[2]["node_position"] >= 3
        assert answers[2]["comparison_choice"] in ["previous", "two_back"]
        assert all(answer["backend"] in ["openrouter", "fallback_bot_response"] for answer in answers)
        assert all("ai_request" in answer and "ai_response" in answer for answer in answers)
