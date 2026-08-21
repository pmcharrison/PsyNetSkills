from __future__ import annotations

from datetime import datetime, timezone


PROFILE_LABELS = [
    "attentive_human_like",
    "inattentive",
    "paste_heavy",
    "fast_low_effort",
    "mock_llm_assisted",
    "browser_agent_like",
]


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_synthetic_telemetry(profile_label: str, trial_id: str) -> dict:
    """Create labeled telemetry for bots and simulated local participants."""
    base = {
        "trial_id": trial_id,
        "page_load_time": utc_now(),
        "trial_start_time": utc_now(),
        "submission_time": utc_now(),
        "source": "synthetic_bot",
    }
    profiles = {
        "attentive_human_like": {
            "response_latency_ms": 28000,
            "focus_event_count": 0,
            "visibility_event_count": 0,
            "paste_count": 0,
            "keydown_count": 180,
            "edit_count": 35,
            "text_growth_sample_count": 8,
        },
        "inattentive": {
            "response_latency_ms": 65000,
            "focus_event_count": 4,
            "visibility_event_count": 3,
            "paste_count": 0,
            "keydown_count": 32,
            "edit_count": 9,
            "text_growth_sample_count": 4,
        },
        "paste_heavy": {
            "response_latency_ms": 12000,
            "focus_event_count": 1,
            "visibility_event_count": 1,
            "paste_count": 3,
            "keydown_count": 8,
            "edit_count": 4,
            "text_growth_sample_count": 3,
        },
        "fast_low_effort": {
            "response_latency_ms": 2800,
            "focus_event_count": 0,
            "visibility_event_count": 0,
            "paste_count": 0,
            "keydown_count": 16,
            "edit_count": 3,
            "text_growth_sample_count": 2,
        },
        "mock_llm_assisted": {
            "response_latency_ms": 7000,
            "focus_event_count": 2,
            "visibility_event_count": 2,
            "paste_count": 1,
            "keydown_count": 11,
            "edit_count": 5,
            "text_growth_sample_count": 3,
        },
        "browser_agent_like": {
            "response_latency_ms": 1500,
            "focus_event_count": 0,
            "visibility_event_count": 0,
            "paste_count": 0,
            "keydown_count": 0,
            "edit_count": 1,
            "text_growth_sample_count": 1,
        },
    }
    base.update(profiles.get(profile_label, profiles["attentive_human_like"]))
    base["focus_events"] = [
        {"trial_id": trial_id, "event": "blur", "elapsed_ms": 4000, "time": utc_now()},
        {"trial_id": trial_id, "event": "focus", "elapsed_ms": 9000, "time": utc_now()},
    ][: base["focus_event_count"]]
    base["visibility_events"] = [
        {"trial_id": trial_id, "state": "hidden", "elapsed_ms": 4200, "time": utc_now()},
        {"trial_id": trial_id, "state": "visible", "elapsed_ms": 9100, "time": utc_now()},
    ][: base["visibility_event_count"]]
    base["paste_events"] = [
        {"trial_id": trial_id, "elapsed_ms": 3000 + i * 200, "text_length": 120, "time": utc_now()}
        for i in range(base["paste_count"])
    ]
    base["text_growth"] = [
        {"trial_id": trial_id, "elapsed_ms": i * 1000, "length": (i + 1) * 20}
        for i in range(base["text_growth_sample_count"])
    ]
    return base
