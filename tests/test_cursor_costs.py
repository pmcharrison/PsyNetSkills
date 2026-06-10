import json
from datetime import datetime, timezone
from pathlib import Path

from psynetsk_tools.cursor_costs import import_cursor_costs


def write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def psynet_metadata() -> dict[str, object]:
    return {
        "checkout_path": "~/PsyNet",
        "branch": "master",
        "commit": "abc123",
        "version": "12.3.0",
        "updated_from": "origin/master",
        "updated_at": "2026-06-06T20:21:00Z",
        "update_command": "git pull --ff-only origin master",
        "dirty": False,
    }


def write_attempt(
    root: Path,
    *,
    slug: str = "example",
    name: str = "2026-06-10-10-00",
    cursor_conversation_id: str | None = "bc-exact",
    run_cost: object | None = None,
) -> Path:
    attempt_dir = root / "challenges" / slug / "attempts" / name
    metadata = {
        "authors": ["pmcharrison"],
        "agent": "Cursor Cloud Agent",
        "client": "cursor",
        "model": "GPT-5.5",
        "started_at": "2026-06-10T10:00:00Z",
        "cursor_conversation_id": cursor_conversation_id,
        "psynet": psynet_metadata(),
    }
    if run_cost is not None:
        metadata["run_cost"] = run_cost
    write(attempt_dir / "agent.json", json.dumps(metadata) + "\n")
    write(
        attempt_dir / "TIMELINE.md",
        "# Timeline\n\n"
        "- T+00:00:00 [agent-start] Started.\n"
        "- T+00:20:00 [agent-stop] Finished.\n",
    )
    return attempt_dir


def write_cursor_csv(path: Path) -> None:
    write(
        path,
        "Date,User,Cloud Agent ID,Automation ID,Kind,Model,Max Mode,"
        "Input (w/ Cache Write),Input (w/o Cache Write),Cache Read,"
        "Output Tokens,Total Tokens,Cost\n"
        "2026-06-10T10:03:00.000Z,user@example.com,bc-exact,,On-Demand,"
        "gpt-5.5-high,Yes,0,100,20,10,130,0.25\n"
        "2026-06-10T10:10:00.000Z,user@example.com,bc-exact,,On-Demand,"
        "gpt-5.5-high,Yes,0,200,30,20,250,0.75\n"
        "2026-06-10T10:12:00.000Z,user@example.com,bc-other,,On-Demand,"
        "gpt-5.5-high,Yes,0,300,40,30,370,1.00\n",
    )


def test_import_cursor_costs_matches_cursor_conversation_id(tmp_path: Path) -> None:
    attempt_dir = write_attempt(tmp_path)
    csv_path = tmp_path / "usage.csv"
    write_cursor_csv(csv_path)

    results = import_cursor_costs(
        root=tmp_path,
        csv_path=csv_path,
        recorded_at=datetime(2026, 6, 10, 11, 0, tzinfo=timezone.utc),
    )

    assert results[0].status == "matched_cloud_agent_id"
    assert results[0].matched_rows == 2
    assert results[0].amount == 1.0
    metadata = json.loads((attempt_dir / "agent.json").read_text(encoding="utf-8"))
    assert metadata["run_cost"]["amount"] == 1.0
    assert metadata["run_cost"]["attribution_status"] == "matched_cloud_agent_id"
    assert metadata["run_cost"]["matched_cloud_agent_ids"] == ["bc-exact"]
    assert metadata["run_cost"]["usage"]["total_tokens"] == 380
    assert metadata["run_cost"]["usage"]["models"]["gpt-5.5-high"]["rows"] == 2


def test_import_cursor_costs_marks_ambiguous_time_window(tmp_path: Path) -> None:
    attempt_dir = write_attempt(tmp_path, cursor_conversation_id=None)
    csv_path = tmp_path / "usage.csv"
    write_cursor_csv(csv_path)

    results = import_cursor_costs(
        root=tmp_path,
        csv_path=csv_path,
        recorded_at=datetime(2026, 6, 10, 11, 0, tzinfo=timezone.utc),
    )

    assert results[0].status == "ambiguous"
    assert results[0].matched_rows == 3
    assert results[0].amount is None
    metadata = json.loads((attempt_dir / "agent.json").read_text(encoding="utf-8"))
    assert metadata["run_cost"]["amount"] is None
    assert metadata["run_cost"]["attribution_status"] == "ambiguous"
    assert metadata["run_cost"]["matched_cloud_agent_ids"] == ["bc-exact", "bc-other"]


def test_import_cursor_costs_skips_existing_run_cost(tmp_path: Path) -> None:
    attempt_dir = write_attempt(
        tmp_path,
        run_cost={
            "currency": "USD",
            "amount": 2.0,
            "source": "manual",
            "recorded_at": "2026-06-10T10:30:00Z",
            "attribution_status": "matched_cloud_agent_id",
        },
    )
    csv_path = tmp_path / "usage.csv"
    write_cursor_csv(csv_path)

    results = import_cursor_costs(root=tmp_path, csv_path=csv_path)

    assert results[0].status == "skipped"
    metadata = json.loads((attempt_dir / "agent.json").read_text(encoding="utf-8"))
    assert metadata["run_cost"]["amount"] == 2.0
