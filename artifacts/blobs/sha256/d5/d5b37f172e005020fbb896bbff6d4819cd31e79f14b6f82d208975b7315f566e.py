import os
from types import SimpleNamespace

import pytest

from experiment import (
    ORIGINAL_TASK,
    BotRadioButtonControl,
    build_next_definition,
    sanitize_website,
)

pytest_plugins = ["pytest_dallinger", "pytest_psynet"]
experiment_dir = os.path.dirname(__file__)


@pytest.mark.parametrize("experiment_directory", [experiment_dir], indirect=True)
def test_experiment(launched_experiment):
    launched_experiment.test_experiment()


def clear_openrouter_env(monkeypatch):
    for key in [
        "OPENROUTER_API_KEY",
        "OPENROUTER_MODEL",
        "OPENROUTER_BASE_URL",
        "OPENROUTER_TIMEOUT_SECONDS",
    ]:
        monkeypatch.delenv(key, raising=False)


def test_fallback_chain_transition_history(monkeypatch):
    clear_openrouter_env(monkeypatch)
    seed = {
        "node_position": 0,
        "parent_node_ids": [],
        "source_parent_node_id": None,
        "original_task_instruction": ORIGINAL_TASK,
        "generated_website": None,
        "chain_history": [],
    }

    first = build_next_definition(
        0,
        10,
        seed,
        None,
        {"participant_instruction": "Create a warm one-page portfolio."},
    )
    assert first["node_position"] == 1
    assert first["website_context_label"] == "original portfolio task"
    assert first["ai_backend"] == "fallback"
    assert first["fallback_reason"]
    assert "Authorization" not in first["ai_request_payload"]

    second = build_next_definition(
        1,
        11,
        first,
        SimpleNamespace(id=10, definition=seed),
        {
            "has_suggestions": "yes",
            "participant_instruction": "Improve the project cards and contact section.",
        },
    )
    assert second["node_position"] == 2
    assert second["has_suggestions"] == "yes"
    assert second["website_context"] == first["generated_website"]

    third = build_next_definition(
        2,
        12,
        second,
        SimpleNamespace(id=11, definition=first),
        {
            "selected_comparison_winner": "two_rounds_earlier",
            "participant_instruction": "Carry forward the clearer layout.",
        },
    )
    assert third["selected_comparison_winner"] == "two_rounds_earlier"
    assert third["website_context"] == first["generated_website"]
    assert third["website_context_source_node_id"] == 11
    assert len(third["chain_history"]) == 3


def test_sanitize_website_removes_active_content():
    website, metadata = sanitize_website(
        "<h1 onclick=\"alert(1)\">Hi</h1><script>alert('x')</script>"
    )
    assert "<script" not in website.lower()
    assert "onclick" not in website.lower()
    assert metadata["removed_script"]
    assert metadata["removed_event_handlers"]


def test_bot_radio_button_control_returns_configured_choice():
    control = BotRadioButtonControl(
        ["previous", "two_rounds_earlier"],
        bot_response_choice="two_rounds_earlier",
    )
    assert control.get_bot_response(None, None, None, None) == "two_rounds_earlier"
