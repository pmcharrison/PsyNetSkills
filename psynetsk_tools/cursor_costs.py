"""Import Cursor usage CSV costs into attempt metadata."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from psynetsk_tools.timeline import parse_timeline_entries, parse_timeline_seconds


@dataclass(frozen=True)
class UsageEvent:
    """One row from a Cursor usage CSV export."""

    timestamp: datetime
    user: str
    cloud_agent_id: str
    kind: str
    model: str
    input_with_cache_write: int
    input_without_cache_write: int
    cache_read: int
    output_tokens: int
    total_tokens: int
    cost: float


@dataclass(frozen=True)
class ImportResult:
    """Summary of one attempt cost import decision."""

    attempt_path: Path
    status: str
    matched_rows: int
    amount: float | None
    message: str


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO timestamp from attempt metadata or Cursor CSV."""

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_int(value: str | None) -> int:
    """Parse an integer CSV field, treating blanks as zero."""

    if value is None or not value.strip():
        return 0
    return int(value)


def parse_float(value: str | None) -> float:
    """Parse a float CSV field, treating blanks as zero."""

    if value is None or not value.strip():
        return 0.0
    return float(value)


def read_usage_events(csv_path: Path) -> list[UsageEvent]:
    """Read Cursor team usage events from a dashboard CSV export."""

    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    events: list[UsageEvent] = []
    for row in rows:
        events.append(
            UsageEvent(
                timestamp=parse_timestamp(row["Date"]),
                user=row.get("User", ""),
                cloud_agent_id=row.get("Cloud Agent ID", ""),
                kind=row.get("Kind", ""),
                model=row.get("Model", ""),
                input_with_cache_write=parse_int(row.get("Input (w/ Cache Write)")),
                input_without_cache_write=parse_int(row.get("Input (w/o Cache Write)")),
                cache_read=parse_int(row.get("Cache Read")),
                output_tokens=parse_int(row.get("Output Tokens")),
                total_tokens=parse_int(row.get("Total Tokens")),
                cost=parse_float(row.get("Cost")),
            ),
        )
    return events


def latest_timeline_seconds(timeline_file: Path) -> int | None:
    """Return the latest structured timestamp in an attempt timeline."""

    if not timeline_file.exists():
        return None

    latest: int | None = None
    entries = parse_timeline_entries(timeline_file.read_text(encoding="utf-8"))
    for entry in entries:
        seconds = parse_timeline_seconds(entry.timestamp)
        if seconds is None:
            return None
        latest = seconds if latest is None else max(latest, seconds)
    return latest


def attempt_window(attempt_dir: Path, agent: dict[str, Any]) -> tuple[datetime, datetime] | None:
    """Return the best available absolute time window for an attempt."""

    started_at = agent.get("started_at")
    if not isinstance(started_at, str) or not started_at.strip():
        return None

    start = parse_timestamp(started_at)
    ended_at = agent.get("ended_at")
    if isinstance(ended_at, str) and ended_at.strip():
        return start, parse_timestamp(ended_at)

    latest_seconds = latest_timeline_seconds(attempt_dir / "TIMELINE.md")
    if latest_seconds is None:
        return None
    return start, start + timedelta(seconds=latest_seconds)


def event_totals(events: list[UsageEvent]) -> dict[str, Any]:
    """Summarize matched Cursor usage events for committed metadata."""

    models: dict[str, dict[str, int | float]] = {}
    for event in events:
        model = models.setdefault(
            event.model or "unknown",
            {
                "rows": 0,
                "input_with_cache_write": 0,
                "input_without_cache_write": 0,
                "cache_read": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "cost": 0.0,
            },
        )
        model["rows"] = int(model["rows"]) + 1
        model["input_with_cache_write"] = (
            int(model["input_with_cache_write"]) + event.input_with_cache_write
        )
        model["input_without_cache_write"] = (
            int(model["input_without_cache_write"]) + event.input_without_cache_write
        )
        model["cache_read"] = int(model["cache_read"]) + event.cache_read
        model["output_tokens"] = int(model["output_tokens"]) + event.output_tokens
        model["total_tokens"] = int(model["total_tokens"]) + event.total_tokens
        model["cost"] = round(float(model["cost"]) + event.cost, 2)

    return {
        "rows": len(events),
        "input_with_cache_write": sum(event.input_with_cache_write for event in events),
        "input_without_cache_write": sum(
            event.input_without_cache_write for event in events
        ),
        "cache_read": sum(event.cache_read for event in events),
        "output_tokens": sum(event.output_tokens for event in events),
        "total_tokens": sum(event.total_tokens for event in events),
        "models": models,
    }


def build_run_cost(
    *,
    events: list[UsageEvent],
    status: str,
    source: str,
    recorded_at: datetime,
    attempt_window_value: tuple[datetime, datetime] | None,
    notes: list[str],
) -> dict[str, Any]:
    """Build the ``run_cost`` metadata block."""

    amount = round(sum(event.cost for event in events), 2) if events else None
    cloud_agent_ids = sorted(
        {event.cloud_agent_id for event in events if event.cloud_agent_id}
    )
    event_times = [event.timestamp for event in events]
    window_started_at = attempt_window_value[0] if attempt_window_value else None
    window_ended_at = attempt_window_value[1] if attempt_window_value else None

    return {
        "currency": "USD",
        "amount": amount,
        "source": source,
        "recorded_at": recorded_at.isoformat().replace("+00:00", "Z"),
        "attribution_status": status,
        "window_started_at": (
            window_started_at.isoformat().replace("+00:00", "Z")
            if window_started_at
            else None
        ),
        "window_ended_at": (
            window_ended_at.isoformat().replace("+00:00", "Z")
            if window_ended_at
            else None
        ),
        "matched_started_at": (
            min(event_times).isoformat().replace("+00:00", "Z") if event_times else None
        ),
        "matched_ended_at": (
            max(event_times).isoformat().replace("+00:00", "Z") if event_times else None
        ),
        "matched_cloud_agent_ids": cloud_agent_ids,
        "usage": event_totals(events),
        "notes": notes,
    }


def select_events_for_attempt(
    agent: dict[str, Any],
    attempt_dir: Path,
    events: list[UsageEvent],
    window_padding: timedelta,
) -> tuple[list[UsageEvent], str, list[str], tuple[datetime, datetime] | None]:
    """Select matching usage events and describe attribution confidence."""

    window = attempt_window(attempt_dir, agent)
    cursor_conversation_id = agent.get("cursor_conversation_id")
    if not isinstance(cursor_conversation_id, str) or not cursor_conversation_id.strip():
        cursor_conversation_id = agent.get("cloud_agent_id")

    if isinstance(cursor_conversation_id, str) and cursor_conversation_id.strip():
        matched = [
            event
            for event in events
            if event.cloud_agent_id == cursor_conversation_id.strip()
            and (
                window is None
                or window[0] - window_padding
                <= event.timestamp
                <= window[1] + window_padding
            )
        ]
        notes = [
            "Matched Cursor CSV rows by cursor_conversation_id.",
        ]
        if window is not None:
            notes.append("Applied attempt time window plus padding.")
        return matched, "matched_cloud_agent_id", notes, window

    if window is None:
        return (
            [],
            "unavailable",
            ["No cursor_conversation_id or complete attempt time window was available."],
            window,
        )

    start, end = window
    matched = [
        event
        for event in events
        if start - window_padding <= event.timestamp <= end + window_padding
    ]
    cloud_agent_ids = sorted(
        {event.cloud_agent_id for event in matched if event.cloud_agent_id}
    )
    if len(cloud_agent_ids) == 1:
        return (
            matched,
            "matched_time_window",
            [
                "Matched Cursor CSV rows by attempt time window.",
                "Only one non-empty Cloud Agent ID appeared in the window.",
            ],
            window,
        )

    return (
        matched,
        "ambiguous",
        [
            "Matched rows by attempt time window, but multiple or no Cloud Agent "
            "IDs appeared. Record cursor_conversation_id in future attempts for "
            "exact attribution.",
        ],
        window,
    )


def import_cursor_costs(
    *,
    root: Path,
    csv_path: Path,
    dry_run: bool = False,
    force: bool = False,
    window_padding_minutes: int = 5,
    recorded_at: datetime | None = None,
) -> list[ImportResult]:
    """Import missing ``run_cost`` metadata from a Cursor usage CSV."""

    events = read_usage_events(csv_path)
    recorded = recorded_at or datetime.now(timezone.utc)
    padding = timedelta(minutes=window_padding_minutes)
    results: list[ImportResult] = []

    for agent_file in sorted(root.glob("challenges/*/attempts/*/agent.json")):
        attempt_dir = agent_file.parent
        try:
            agent = json.loads(agent_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            results.append(
                ImportResult(attempt_dir, "error", 0, None, f"invalid JSON: {exc}"),
            )
            continue
        if not isinstance(agent, dict):
            results.append(ImportResult(attempt_dir, "error", 0, None, "not an object"))
            continue

        existing_run_cost = agent.get("run_cost")
        if existing_run_cost is not None and not force:
            results.append(ImportResult(attempt_dir, "skipped", 0, None, "has run_cost"))
            continue

        matched, status, notes, window = select_events_for_attempt(
            agent,
            attempt_dir,
            events,
            padding,
        )
        run_cost = build_run_cost(
            events=matched,
            status=status,
            source="cursor_usage_csv_batch_import",
            recorded_at=recorded,
            attempt_window_value=window,
            notes=notes,
        )
        if status in {"ambiguous", "unavailable"}:
            run_cost["amount"] = None

        if not dry_run:
            agent["run_cost"] = run_cost
            agent_file.write_text(json.dumps(agent, indent=2) + "\n", encoding="utf-8")

        results.append(
            ImportResult(
                attempt_path=attempt_dir,
                status=status,
                matched_rows=len(matched),
                amount=run_cost["amount"],
                message="updated" if not dry_run else "dry run",
            ),
        )

    return results


def main(argv: list[str] | None = None) -> int:
    """Run the Cursor cost CSV importer."""

    parser = argparse.ArgumentParser(
        description="Import Cursor usage CSV costs into attempt agent.json files.",
    )
    parser.add_argument("csv_path", type=Path, help="Cursor usage CSV export path")
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root")
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing run_cost metadata",
    )
    parser.add_argument(
        "--window-padding-minutes",
        type=int,
        default=5,
        help="Padding around attempt windows for CSV row matching",
    )
    args = parser.parse_args(argv)

    results = import_cursor_costs(
        root=args.root,
        csv_path=args.csv_path,
        dry_run=args.dry_run,
        force=args.force,
        window_padding_minutes=args.window_padding_minutes,
    )
    for result in results:
        amount = "N/A" if result.amount is None else f"${result.amount:.2f}"
        print(
            f"{result.status}: {result.attempt_path} "
            f"rows={result.matched_rows} amount={amount} ({result.message})",
        )
    return 1 if any(result.status == "error" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
