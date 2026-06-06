from psynetsk_tools.timeline import (
    format_duration,
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
