import json
import math
import os
import re
import urllib.error
import urllib.request
from typing import Callable, Dict, List, Mapping, Optional

from dallinger.config import get_config
from psynet.bot import BotResponse

COLORS = ["red", "green", "blue"]

HYBRID_CONFIG_DEFAULTS = {
    "ai_participant_proportion": 0.0,
    "ai_total_participant_target": 6,
    "openrouter_api_key_env_var": "OPENROUTER_API_KEY",
    "openrouter_model": "openai/gpt-4o-mini",
    "openrouter_base_url": "https://openrouter.ai/api/v1/chat/completions",
    "openrouter_timeout_seconds": 20.0,
    "openrouter_max_retries": 1,
    "openrouter_mock_mode": True,
}


def _read_config_value(config, key, default):
    if config is None:
        config = get_config()
    if isinstance(config, Mapping):
        return config.get(key, default)
    return config.get(key, default=default)


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value = value.strip().lower()
        if value in {"true", "1", "yes", "y"}:
            return True
        if value in {"false", "0", "no", "n"}:
            return False
    raise ValueError(f"Cannot interpret {value!r} as a boolean.")


def get_hybrid_config(config=None) -> Dict[str, object]:
    settings = {
        key: _read_config_value(config, key, default)
        for key, default in HYBRID_CONFIG_DEFAULTS.items()
    }
    settings["ai_participant_proportion"] = float(
        settings["ai_participant_proportion"]
    )
    settings["ai_total_participant_target"] = int(
        settings["ai_total_participant_target"]
    )
    settings["openrouter_timeout_seconds"] = float(
        settings["openrouter_timeout_seconds"]
    )
    settings["openrouter_max_retries"] = int(settings["openrouter_max_retries"])
    settings["openrouter_mock_mode"] = _as_bool(settings["openrouter_mock_mode"])
    validate_hybrid_config(settings)
    return settings


def validate_hybrid_config(settings: Mapping[str, object]):
    proportion = settings["ai_participant_proportion"]
    if not 0 <= proportion <= 100:
        raise ValueError("ai_participant_proportion must be between 0 and 100.")
    if settings["ai_total_participant_target"] < 0:
        raise ValueError("ai_total_participant_target must be non-negative.")
    if not str(settings["openrouter_api_key_env_var"]).strip():
        raise ValueError("openrouter_api_key_env_var must name an environment variable.")
    if not str(settings["openrouter_model"]).strip():
        raise ValueError("openrouter_model must be non-empty.")
    if not str(settings["openrouter_base_url"]).startswith(("http://", "https://")):
        raise ValueError("openrouter_base_url must be an HTTP(S) URL.")
    if settings["openrouter_timeout_seconds"] <= 0:
        raise ValueError("openrouter_timeout_seconds must be positive.")
    if settings["openrouter_max_retries"] < 0:
        raise ValueError("openrouter_max_retries must be non-negative.")
    if not settings["openrouter_mock_mode"] and not os.environ.get(
        str(settings["openrouter_api_key_env_var"])
    ):
        raise ValueError(
            "OpenRouter live mode requires the configured API key environment variable."
        )


def plan_ai_launches(
    *,
    human_count: int,
    ai_count: int,
    ai_running: int,
    total_participant_target: int,
    ai_participant_proportion: float,
) -> int:
    if min(human_count, ai_count, ai_running, total_participant_target) < 0:
        raise ValueError("Participant counts must be non-negative.")
    if not 0 <= ai_participant_proportion <= 100:
        raise ValueError("ai_participant_proportion must be between 0 and 100.")

    current_ai = ai_count + ai_running
    current_total = human_count + current_ai
    remaining_capacity = total_participant_target - current_total
    if remaining_capacity <= 0 or ai_participant_proportion == 0:
        return 0
    if ai_participant_proportion == 100:
        return remaining_capacity

    desired_ai_for_current_humans = math.ceil(
        human_count * ai_participant_proportion / (100 - ai_participant_proportion)
    )
    needed = desired_ai_for_current_humans - current_ai
    return max(0, min(needed, remaining_capacity))


def build_color_stimulus(
    *,
    target: str,
    participant_group: str,
    active_index: int,
    starting_values: List[int],
) -> Dict[str, object]:
    if not 0 <= active_index < len(COLORS):
        raise ValueError("active_index must select one of the RGB channels.")
    if len(starting_values) != len(COLORS):
        raise ValueError("starting_values must contain red, green, and blue values.")
    rgb = {color: int(value) for color, value in zip(COLORS, starting_values)}
    for value in rgb.values():
        if not 0 <= value <= 255:
            raise ValueError("RGB values must be between 0 and 255.")
    return {
        "target": target,
        "participant_group": participant_group,
        "active_color": COLORS[active_index],
        "active_index": active_index,
        "rgb": rgb,
    }


def build_human_prompt_html(stimulus: Mapping[str, object]) -> str:
    return (
        f"<h3 id='participant-group'>Participant group = "
        f"{stimulus['participant_group']}</h3>"
        "<p>Adjust the slider to match the following word as well as possible: "
        f"<strong>{stimulus['target']}</strong></p>"
    )


def format_ai_prompt(stimulus: Mapping[str, object]) -> str:
    rgb = stimulus["rgb"]
    return (
        "You are completing the same color-slider task as a human participant.\n"
        f"Participant group = {stimulus['participant_group']}.\n"
        "Adjust the slider to match the following word as well as possible: "
        f"{stimulus['target']}.\n"
        "The displayed color square is represented by these RGB values: "
        f"red={rgb['red']}, green={rgb['green']}, blue={rgb['blue']}.\n"
        f"You may adjust only the {stimulus['active_color']} channel.\n"
        "Return exactly one JSON object in this format: {\"value\": 0}.\n"
        "The value must be an integer from 0 to 255."
    )


def parse_ai_slider_response(content: str) -> int:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        matches = re.findall(r"-?\d+", content)
        if len(matches) != 1:
            raise ValueError("AI response must contain exactly one slider value.")
        value = int(matches[0])
    else:
        if not isinstance(parsed, Mapping) or set(parsed) != {"value"}:
            raise ValueError("AI response JSON must contain only a 'value' field.")
        value = int(parsed["value"])
    if not 0 <= value <= 255:
        raise ValueError("AI slider value must be between 0 and 255.")
    return value


def mock_openrouter_content(stimulus: Mapping[str, object]) -> str:
    rgb = stimulus["rgb"]
    value = (
        sum(ord(char) for char in str(stimulus["target"]))
        + rgb[str(stimulus["active_color"])]
        + 31 * int(stimulus["active_index"])
    ) % 256
    return json.dumps({"value": value})


def request_openrouter_content(
    prompt: str,
    settings: Mapping[str, object],
    request_fn: Optional[Callable] = None,
) -> str:
    payload = json.dumps(
        {
            "model": settings["openrouter_model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 20,
        }
    ).encode("utf-8")
    api_key = os.environ[str(settings["openrouter_api_key_env_var"])]
    request = urllib.request.Request(
        str(settings["openrouter_base_url"]),
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    last_error = None
    for _ in range(int(settings["openrouter_max_retries"]) + 1):
        try:
            if request_fn is None:
                with urllib.request.urlopen(
                    request,
                    timeout=float(settings["openrouter_timeout_seconds"]),
                ) as response:
                    response_payload = response.read().decode("utf-8")
            else:
                response_payload = request_fn(
                    request,
                    timeout=float(settings["openrouter_timeout_seconds"]),
                )
            if isinstance(response_payload, Mapping):
                data = response_payload
            else:
                data = json.loads(response_payload)
            return data["choices"][0]["message"]["content"]
        except (
            KeyError,
            IndexError,
            TypeError,
            json.JSONDecodeError,
            urllib.error.URLError,
        ) as error:
            last_error = error
    raise RuntimeError(f"OpenRouter request failed: {last_error}")


def bot_response(
    stimulus: Mapping[str, object],
    config=None,
    request_fn: Optional[Callable] = None,
) -> BotResponse:
    settings = get_hybrid_config(config)
    prompt = format_ai_prompt(stimulus)
    if settings["openrouter_mock_mode"]:
        content = mock_openrouter_content(stimulus)
    else:
        content = request_openrouter_content(prompt, settings, request_fn)
    value = parse_ai_slider_response(content)
    return BotResponse(
        answer=value,
        metadata={
            "participant_role": "ai",
            "ai_prompt": prompt,
            "ai_stimulus": dict(stimulus),
            "openrouter_model": settings["openrouter_model"],
            "openrouter_mock_mode": settings["openrouter_mock_mode"],
        },
    )
