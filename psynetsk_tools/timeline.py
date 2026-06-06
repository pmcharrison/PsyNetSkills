"""Parse attempt timelines and summarize agent implementation time."""

from __future__ import annotations

import re
from dataclasses import dataclass

TIMELINE_ENTRY_RE = re.compile(
    r"^- (?P<timestamp>T\+\d{2}:\d{2}:\d{2}) "
    r"\[(?P<actor>agent-start|agent|agent-stop|manual|system)\] "
    r"(?P<description>.+)$"
)


@dataclass(frozen=True)
class TimelineEntry:
    """A structured attempt timeline entry."""

    timestamp: str
    actor: str
    description: str


def parse_timeline_entries(markdown: str) -> list[TimelineEntry]:
    """Parse structured entries from ``TIMELINE.md``."""
    entries: list[TimelineEntry] = []
    for line in markdown.splitlines():
        match = TIMELINE_ENTRY_RE.fullmatch(line)
        if match is None:
            continue
        entries.append(
            TimelineEntry(
                timestamp=match.group("timestamp"),
                actor=match.group("actor"),
                description=match.group("description"),
            )
        )
    return entries


def parse_timeline_seconds(timestamp: str) -> int | None:
    """Parse a relative ``T+HH:MM:SS`` timestamp into seconds."""
    match = re.fullmatch(r"T\+(\d{2}):(\d{2}):(\d{2})", timestamp)
    if match is None:
        return None
    hours, minutes, seconds = (int(part) for part in match.groups())
    if minutes >= 60 or seconds >= 60:
        return None
    return hours * 3600 + minutes * 60 + seconds


def implementation_time_seconds(entries: list[TimelineEntry]) -> int | None:
    """Return active agent implementation time, excluding manual gaps."""
    total = 0
    active_start: int | None = None
    previous_seconds: int | None = None

    for entry in entries:
        current_seconds = parse_timeline_seconds(entry.timestamp)
        if current_seconds is None:
            return None
        if previous_seconds is not None and current_seconds < previous_seconds:
            return None
        previous_seconds = current_seconds

        if entry.actor == "agent-start":
            if active_start is not None:
                return None
            active_start = current_seconds
        elif entry.actor == "agent-stop":
            if active_start is None:
                return None
            total += current_seconds - active_start
            active_start = None

    if active_start is not None or total == 0:
        return None
    return total


def format_duration(seconds: int | None) -> str:
    """Format a duration as compact hours/minutes/seconds text."""
    if seconds is None:
        return "Not recorded"

    hours, remainder = divmod(seconds, 3600)
    minutes, remaining_seconds = divmod(remainder, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours}h")
    if minutes or hours:
        parts.append(f"{minutes}m")
    parts.append(f"{remaining_seconds}s")
    return " ".join(parts)
