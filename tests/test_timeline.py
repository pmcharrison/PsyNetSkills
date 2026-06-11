from psynetsk_tools.timeline import (
    format_duration,
    format_human_intervention_count,
    human_intervention_count,
    implementation_time_seconds,
    parse_timeline_entries,
)


def test_implementation_time_sums_agent_start_stop_segments() -> None:
    entries = parse_timeline_entries(
        "# Timeline\n\n"
        "- T+00:00:00 [agent-start] Started.\n"
        "- T+00:10:00 [agent-stop] Paused.\n"
        "- T+00:25:00 [manual] User gave feedback.\n"
        "- T+00:30:00 [agent-start] Resumed.\n"
        "- T+01:00:05 [agent-stop] Finished.\n"
    )

    assert implementation_time_seconds(entries) == 2405
    assert format_duration(2405) == "40m 5s"


def test_implementation_time_is_missing_for_incomplete_segment() -> None:
    entries = parse_timeline_entries(
        "# Timeline\n\n"
        "- T+00:00:00 [agent-start] Started.\n"
        "- T+00:10:00 [agent] Implemented scaffold.\n"
    )

    assert implementation_time_seconds(entries) is None
    assert format_duration(None) == "Not recorded"


def test_human_intervention_count_uses_manual_intervention_tag() -> None:
    entries = parse_timeline_entries(
        "# Timeline\n\n"
        "- T+00:00:00 [agent-start] Started.\n"
        "- T+00:05:00 [manual] User asked for status.\n"
        "- T+00:06:00 [manual] [intervention] User redirected the implementation.\n"
        "- T+00:10:00 [system] [blocker] Test environment was unavailable.\n"
        "- T+00:12:00 [agent-stop] Finished.\n"
    )

    assert entries[1].tags == []
    assert entries[2].tags == ["intervention"]
    assert entries[2].description == "User redirected the implementation."
    assert human_intervention_count(entries) == 1
    assert format_human_intervention_count(1) == "1"


def test_human_intervention_count_is_missing_without_structured_entries() -> None:
    assert human_intervention_count([]) is None
    assert format_human_intervention_count(None) == "Not recorded"
