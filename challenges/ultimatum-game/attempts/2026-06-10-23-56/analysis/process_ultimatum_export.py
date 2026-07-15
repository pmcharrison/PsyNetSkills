#!/usr/bin/env python3
"""Process the exported repeated Ultimatum game data into analysis tables."""

from __future__ import annotations

import argparse
import csv
import io
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PLAYER_COLUMNS = [
    "deployment_id",
    "export_scope",
    "session_id",
    "dyad_id",
    "sync_group_id",
    "round_index",
    "history_index",
    "counted_round_index",
    "round_counted",
    "round_skipped",
    "timeout_role",
    "decision",
    "offer",
    "offer_fraction",
    "accepted",
    "participant_id",
    "player_order",
    "role",
    "partner_participant_id",
    "partner_role",
    "player_action_type",
    "player_action_value",
    "player_timed_out",
    "partner_timed_out",
    "player_round_score",
    "partner_round_score",
    "dyad_round_score",
    "player_cumulative_score",
    "partner_cumulative_score",
    "player_final_score",
    "partner_final_score",
    "session_counted_rounds",
    "session_timeout_count",
    "session_status",
    "completion_reason",
    "trial_id",
    "response_id",
    "trial_failed",
    "participant_failed",
    "participant_status",
    "performance_reward",
    "round_events_json",
    "round_state_json",
]

ROUND_COLUMNS = [
    "deployment_id",
    "export_scope",
    "session_id",
    "dyad_id",
    "sync_group_id",
    "round_index",
    "history_index",
    "counted_round_index",
    "round_counted",
    "round_skipped",
    "timeout_role",
    "decision",
    "offer",
    "offer_fraction",
    "accepted",
    "proposer_id",
    "responder_id",
    "proposer_payoff",
    "responder_payoff",
    "dyad_round_score",
    "proposer_cumulative_score",
    "responder_cumulative_score",
    "session_counted_rounds",
    "session_timeout_count",
    "session_status",
    "completion_reason",
    "round_events_json",
    "round_state_json",
]

DATA_DICTIONARY = {
    "deployment_id": "Exported PsyNet deployment identifier; used as the experimental batch ID.",
    "export_scope": "Archive namespace used as input, normally regular.",
    "session_id": "UltimatumSession row ID in the export.",
    "dyad_id": "Stable dyad identifier, equal to the PsyNet sync group/session group_id.",
    "sync_group_id": "SimpleSyncGroup row ID joined from dyad_id.",
    "round_index": "Round number from the session history, including skipped timeout rounds.",
    "history_index": "Zero-based position of the round in UltimatumSession.state_json.history.",
    "counted_round_index": "One-based index among non-skipped scored rounds; blank for skipped rounds.",
    "round_counted": "True when the round produced a scored decision and counted toward completion.",
    "round_skipped": "True when the round was skipped, currently because of a timeout.",
    "timeout_role": "Role that timed out for skipped rounds; blank otherwise.",
    "decision": "Round decision: accept, reject, or timeout.",
    "offer": "Coin offer made by the proposer; blank if no offer was accepted by the server.",
    "offer_fraction": "Offer divided by the 10-coin endowment when offer is present.",
    "accepted": "True for accepted offers, False for rejected offers, blank for skipped rounds.",
    "participant_id": "PsyNet participant ID for this player row.",
    "player_order": "Stable zero-based order from the session participant list sorted by participant ID.",
    "role": "Participant role in this round: proposer or responder.",
    "partner_participant_id": "The other participant in the dyad.",
    "partner_role": "Partner role in this round.",
    "player_action_type": "Player-level action represented by the row: offer, decision, timeout, or partner_timeout.",
    "player_action_value": "Offer amount, decision value, or timeout marker matching player_action_type.",
    "player_timed_out": "True when this participant held the role that timed out.",
    "partner_timed_out": "True when the partner held the role that timed out.",
    "player_round_score": "Coins earned by the participant in this round.",
    "partner_round_score": "Coins earned by the partner in this round.",
    "dyad_round_score": "Sum of both players' round scores.",
    "player_cumulative_score": "Participant cumulative score after this round.",
    "partner_cumulative_score": "Partner cumulative score after this round.",
    "player_final_score": "Participant final score from the completed session state.",
    "partner_final_score": "Partner final score from the completed session state.",
    "session_counted_rounds": "Final counted-round total recorded in the session state.",
    "session_timeout_count": "Final timeout count recorded in the session state.",
    "session_status": "Final session status, such as complete or failed.",
    "completion_reason": "Final completion reason recorded in the session state.",
    "trial_id": "GameTrial row ID for this participant's live game trial.",
    "response_id": "Response row ID associated with the participant's GameTrial answer.",
    "trial_failed": "Failure flag on the participant's GameTrial row.",
    "participant_failed": "Failure flag on the Participant row.",
    "participant_status": "Participant status from the export.",
    "performance_reward": "Participant performance reward recorded by PsyNet.",
    "round_events_json": "JSON list of session events with this round_index.",
    "round_state_json": "Original JSON object for this history round.",
    "proposer_id": "Participant assigned as proposer in the round.",
    "responder_id": "Participant assigned as responder in the round.",
    "proposer_payoff": "Coins earned by the proposer in the round.",
    "responder_payoff": "Coins earned by the responder in the round.",
    "proposer_cumulative_score": "Proposer cumulative score after this round.",
    "responder_cumulative_score": "Responder cumulative score after this round.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--export-zip",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "evidence" / "data.zip",
        help="Path to a PsyNet data.zip export.",
    )
    parser.add_argument(
        "--scope",
        default="regular",
        choices=["regular", "anonymous"],
        help="Export scope to process from the archive.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Directory for clean outputs.",
    )
    return parser.parse_args()


def read_csv_from_zip(archive: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    with archive.open(name) as handle:
        text = io.TextIOWrapper(handle, encoding="utf-8", newline="")
        return list(csv.DictReader(text))


def parse_json(value: str | None, default: Any) -> Any:
    if value in (None, ""):
        return default
    return json.loads(value)


def maybe_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def maybe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def bool_string(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return "true" if str(value).lower() == "true" else "false"


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return value


def write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column)) for column in columns})


def index_metadata(rows: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    experiment_config = rows.get("ExperimentConfig", [])
    deployment_id = ""
    if experiment_config:
        deployment_id = experiment_config[0].get("deployment_id") or experiment_config[0].get("id") or ""

    trials_by_participant: dict[tuple[int, int], dict[str, Any]] = {}
    for row in rows.get("GameTrial", []):
        answer = parse_json(row.get("answer"), {})
        group_id = maybe_int(row.get("group_id")) or maybe_int(answer.get("group_id"))
        participant_id = maybe_int(row.get("participant_id")) or maybe_int(answer.get("participant_id"))
        if group_id is None or participant_id is None:
            continue
        trials_by_participant[(group_id, participant_id)] = {
            "trial_id": row.get("id", ""),
            "response_id": row.get("response_id", ""),
            "trial_failed": bool_string(row.get("failed")),
            "trial_answer": answer,
        }

    participants_by_id = {
        int(row["id"]): row for row in rows.get("Participant", []) if row.get("id")
    }
    sync_groups_by_id = {
        int(row["id"]): row for row in rows.get("SimpleSyncGroup", []) if row.get("id")
    }

    return {
        "deployment_id": deployment_id,
        "trials_by_participant": trials_by_participant,
        "participants_by_id": participants_by_id,
        "sync_groups_by_id": sync_groups_by_id,
    }


def action_for_player(round_state: dict[str, Any], role: str) -> tuple[str, Any]:
    if round_state.get("skipped"):
        timeout_role = round_state.get("timeout_role")
        if role == timeout_role:
            return "timeout", "timeout"
        return "partner_timeout", "partner_timeout"
    if role == "proposer":
        return "offer", round_state.get("offer")
    if role == "responder":
        return "decision", round_state.get("decision")
    return "", ""


def build_outputs(rows: dict[str, list[dict[str, str]]], scope: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    metadata = index_metadata(rows)
    player_rows: list[dict[str, Any]] = []
    round_rows: list[dict[str, Any]] = []
    validation_messages: list[str] = []

    for session in rows.get("UltimatumSession", []):
        state = parse_json(session.get("state_json"), {})
        group_id = int(session["group_id"])
        session_id = session.get("id", "")
        participants = sorted(int(pid) for pid in state.get("participants", []))
        if len(participants) != 2:
            validation_messages.append(
                f"WARNING: session {session_id} has {len(participants)} participant(s), expected 2."
            )
        participant_order = {participant_id: index for index, participant_id in enumerate(participants)}
        events_by_round: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for event in state.get("events", []):
            round_index = event.get("round_index")
            if round_index is not None:
                events_by_round[int(round_index)].append(event)

        counted_round_index = 0
        for history_index, round_state in enumerate(state.get("history", [])):
            round_index = int(round_state["round_index"])
            round_skipped = bool(round_state.get("skipped", False))
            round_counted = not round_skipped
            if round_counted:
                counted_round_index += 1
                counted_value: int | None = counted_round_index
            else:
                counted_value = None

            roles = {str(k): v for k, v in round_state.get("roles", {}).items()}
            proposer_id = next((int(pid) for pid, role in roles.items() if role == "proposer"), None)
            responder_id = next((int(pid) for pid, role in roles.items() if role == "responder"), None)
            payoffs = {str(k): int(v) for k, v in round_state.get("payoffs", {}).items()}
            totals = {str(k): int(v) for k, v in round_state.get("totals", {}).items()}
            offer = maybe_int(round_state.get("offer"))
            offer_fraction = None if offer is None else offer / 10
            accepted = None if round_skipped else round_state.get("decision") == "accept"
            round_events = events_by_round.get(round_index, [])

            round_rows.append(
                {
                    "deployment_id": metadata["deployment_id"],
                    "export_scope": scope,
                    "session_id": session_id,
                    "dyad_id": group_id,
                    "sync_group_id": group_id if group_id in metadata["sync_groups_by_id"] else "",
                    "round_index": round_index,
                    "history_index": history_index,
                    "counted_round_index": counted_value,
                    "round_counted": round_counted,
                    "round_skipped": round_skipped,
                    "timeout_role": round_state.get("timeout_role"),
                    "decision": round_state.get("decision"),
                    "offer": offer,
                    "offer_fraction": offer_fraction,
                    "accepted": accepted,
                    "proposer_id": proposer_id,
                    "responder_id": responder_id,
                    "proposer_payoff": payoffs.get(str(proposer_id), ""),
                    "responder_payoff": payoffs.get(str(responder_id), ""),
                    "dyad_round_score": sum(payoffs.values()),
                    "proposer_cumulative_score": totals.get(str(proposer_id), ""),
                    "responder_cumulative_score": totals.get(str(responder_id), ""),
                    "session_counted_rounds": state.get("counted_rounds"),
                    "session_timeout_count": state.get("timeout_count"),
                    "session_status": state.get("status"),
                    "completion_reason": state.get("completion_reason"),
                    "round_events_json": round_events,
                    "round_state_json": round_state,
                }
            )

            for participant_id in participants:
                partner_id = next(pid for pid in participants if pid != participant_id)
                role = roles.get(str(participant_id), "")
                partner_role = roles.get(str(partner_id), "")
                action_type, action_value = action_for_player(round_state, role)
                participant = metadata["participants_by_id"].get(participant_id, {})
                trial = metadata["trials_by_participant"].get((group_id, participant_id), {})
                player_rows.append(
                    {
                        "deployment_id": metadata["deployment_id"],
                        "export_scope": scope,
                        "session_id": session_id,
                        "dyad_id": group_id,
                        "sync_group_id": group_id if group_id in metadata["sync_groups_by_id"] else "",
                        "round_index": round_index,
                        "history_index": history_index,
                        "counted_round_index": counted_value,
                        "round_counted": round_counted,
                        "round_skipped": round_skipped,
                        "timeout_role": round_state.get("timeout_role"),
                        "decision": round_state.get("decision"),
                        "offer": offer,
                        "offer_fraction": offer_fraction,
                        "accepted": accepted,
                        "participant_id": participant_id,
                        "player_order": participant_order.get(participant_id, ""),
                        "role": role,
                        "partner_participant_id": partner_id,
                        "partner_role": partner_role,
                        "player_action_type": action_type,
                        "player_action_value": action_value,
                        "player_timed_out": role == round_state.get("timeout_role"),
                        "partner_timed_out": partner_role == round_state.get("timeout_role"),
                        "player_round_score": payoffs.get(str(participant_id), 0),
                        "partner_round_score": payoffs.get(str(partner_id), 0),
                        "dyad_round_score": sum(payoffs.values()),
                        "player_cumulative_score": totals.get(str(participant_id), 0),
                        "partner_cumulative_score": totals.get(str(partner_id), 0),
                        "player_final_score": state.get("totals", {}).get(str(participant_id), 0),
                        "partner_final_score": state.get("totals", {}).get(str(partner_id), 0),
                        "session_counted_rounds": state.get("counted_rounds"),
                        "session_timeout_count": state.get("timeout_count"),
                        "session_status": state.get("status"),
                        "completion_reason": state.get("completion_reason"),
                        "trial_id": trial.get("trial_id", ""),
                        "response_id": trial.get("response_id", ""),
                        "trial_failed": trial.get("trial_failed", ""),
                        "participant_failed": bool_string(participant.get("failed")),
                        "participant_status": participant.get("status", ""),
                        "performance_reward": maybe_float(participant.get("performance_reward")),
                        "round_events_json": round_events,
                        "round_state_json": round_state,
                    }
                )

    validation_messages.extend(validate_outputs(player_rows, round_rows, rows))
    return player_rows, round_rows, validation_messages


def validate_outputs(
    player_rows: list[dict[str, Any]],
    round_rows: list[dict[str, Any]],
    rows: dict[str, list[dict[str, str]]],
) -> list[str]:
    messages: list[str] = []
    key_counts = Counter((row["dyad_id"], row["round_index"]) for row in player_rows)
    bad_counts = {key: count for key, count in key_counts.items() if count != 2}
    if bad_counts:
        messages.append(f"FAIL: dyad-round player row counts are not all 2: {bad_counts}")
    else:
        messages.append(f"PASS: {len(key_counts)} dyad-round(s) each have exactly two player rows.")

    duplicate_counts = Counter(
        (row["dyad_id"], row["round_index"], row["participant_id"]) for row in player_rows
    )
    duplicates = {key: count for key, count in duplicate_counts.items() if count > 1}
    if duplicates:
        messages.append(f"FAIL: duplicate player rows found: {duplicates}")
    else:
        messages.append("PASS: no duplicate participant rows within dyad-rounds.")

    partner_errors = []
    rows_by_key = {
        (row["dyad_id"], row["round_index"], row["participant_id"]): row for row in player_rows
    }
    for row in player_rows:
        partner_key = (row["dyad_id"], row["round_index"], row["partner_participant_id"])
        partner = rows_by_key.get(partner_key)
        if partner is None or partner["partner_participant_id"] != row["participant_id"]:
            partner_errors.append((row["dyad_id"], row["round_index"], row["participant_id"]))
    if partner_errors:
        messages.append(f"FAIL: partner symmetry errors found: {partner_errors}")
    else:
        messages.append("PASS: partner fields are symmetric.")

    score_errors = []
    for row in player_rows:
        if int(row["player_round_score"]) + int(row["partner_round_score"]) != int(row["dyad_round_score"]):
            score_errors.append((row["dyad_id"], row["round_index"], row["participant_id"]))
    if score_errors:
        messages.append(f"FAIL: row score sums do not match dyad scores: {score_errors}")
    else:
        messages.append("PASS: player and partner round scores sum to dyad round scores.")

    final_score_errors = []
    for row in player_rows:
        trial_answer = None
        for trial in rows.get("GameTrial", []):
            if trial.get("id") == str(row.get("trial_id")):
                trial_answer = parse_json(trial.get("answer"), {})
                break
        if trial_answer and int(trial_answer.get("total_score", 0)) != int(row["player_final_score"]):
            final_score_errors.append((row["participant_id"], row["trial_id"]))
    if final_score_errors:
        messages.append(f"FAIL: final trial-answer scores do not match session totals: {final_score_errors}")
    else:
        messages.append("PASS: final GameTrial answer scores match session totals.")

    expected_round_rows = len(key_counts)
    if len(round_rows) == expected_round_rows:
        messages.append(f"PASS: round_level.csv has one row for each of {expected_round_rows} dyad-round(s).")
    else:
        messages.append(
            f"FAIL: round_level.csv has {len(round_rows)} row(s), expected {expected_round_rows}."
        )
    return messages


def write_dictionary(path: Path) -> None:
    columns = []
    seen = set()
    for column in PLAYER_COLUMNS + ROUND_COLUMNS:
        if column not in seen:
            seen.add(column)
            columns.append(column)
    lines = [
        "# Data dictionary",
        "",
        "These columns describe the processed repeated Ultimatum game export.",
        "",
        "| Column | Description |",
        "| --- | --- |",
    ]
    for column in columns:
        lines.append(f"| `{column}` | {DATA_DICTIONARY[column]} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def markdown_table(rows: list[dict[str, Any]], columns: list[str], limit: int = 6) -> str:
    selected = rows[:limit]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in selected:
        lines.append("| " + " | ".join(str(csv_value(row.get(column))) for column in columns) + " |")
    return "\n".join(lines)


def write_report(
    path: Path,
    export_zip: Path,
    scope: str,
    rows: dict[str, list[dict[str, str]]],
    player_rows: list[dict[str, Any]],
    round_rows: list[dict[str, Any]],
    validation_messages: list[str],
) -> None:
    table_counts = {name: len(table_rows) for name, table_rows in sorted(rows.items())}
    complete_participants = sum(
        1 for participant in rows.get("Participant", []) if participant.get("failed") == "False"
    )
    failed_participants = sum(
        1 for participant in rows.get("Participant", []) if participant.get("failed") == "True"
    )
    preview_columns = [
        "dyad_id",
        "round_index",
        "participant_id",
        "role",
        "partner_participant_id",
        "player_action_type",
        "player_action_value",
        "player_round_score",
        "player_cumulative_score",
        "round_skipped",
    ]
    round_preview_columns = [
        "dyad_id",
        "round_index",
        "proposer_id",
        "responder_id",
        "offer",
        "decision",
        "round_skipped",
        "dyad_round_score",
    ]
    lines = [
        "# Ultimatum export processing report",
        "",
        "## Source",
        "",
        f"- Export archive: `{export_zip}`",
        f"- Export scope: `{scope}`",
        "- Authoritative round ledger: `regular/data/UltimatumSession.csv` field `state_json.history`.",
        "- Trial audit pointers: `regular/data/GameTrial.csv` fields `id`, `response_id`, and `answer`.",
        "- Participant audit pointers: `regular/data/Participant.csv` fields `failed`, `status`, and `performance_reward`.",
        "",
        "## Source table counts",
        "",
    ]
    lines.extend(f"- `{name}`: {count}" for name, count in table_counts.items())
    lines.extend(
        [
            "",
            "## Missingness and exclusions",
            "",
            f"- Completed participants represented in dyadic rows: {complete_participants}.",
            f"- Failed pre-pairing participants excluded from dyadic rows: {failed_participants}.",
            "- Skipped timeout rounds are retained with `round_skipped=true`, `decision=timeout`, zero round scores, and blank `counted_round_index`.",
            "- There were no accepted server actions for timed-out rounds in the session event log; the timeout role is represented as `player_action_type=timeout` for the timed-out role and `partner_timeout` for the other player.",
            "",
            "## Player-round preview",
            "",
            markdown_table(player_rows, preview_columns),
            "",
            "## Round-level preview",
            "",
            markdown_table(round_rows, round_preview_columns),
            "",
            "## Validation",
            "",
        ]
    )
    lines.extend(f"- {message}" for message in validation_messages)
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            "- `clean_round_player.csv`: one row per dyad, round, and player.",
            "- `round_level.csv`: one row per dyad and round.",
            "- `DATA_DICTIONARY.md`: column definitions for both processed tables.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    prefix = f"{args.scope}/data/"
    table_names = [
        "UltimatumSession",
        "GameTrial",
        "Participant",
        "ParticipantLinkSyncGroup",
        "SimpleSyncGroup",
        "ExperimentConfig",
    ]

    with zipfile.ZipFile(args.export_zip) as archive:
        rows = {name: read_csv_from_zip(archive, f"{prefix}{name}.csv") for name in table_names}

    player_rows, round_rows, validation_messages = build_outputs(rows, args.scope)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "clean_round_player.csv", PLAYER_COLUMNS, player_rows)
    write_csv(args.out_dir / "round_level.csv", ROUND_COLUMNS, round_rows)
    write_dictionary(args.out_dir / "DATA_DICTIONARY.md")
    write_report(
        args.out_dir / "PROCESSING_REPORT.md",
        args.export_zip,
        args.scope,
        rows,
        player_rows,
        round_rows,
        validation_messages,
    )

    print(f"Wrote {len(player_rows)} player-round rows to {args.out_dir / 'clean_round_player.csv'}")
    print(f"Wrote {len(round_rows)} round-level rows to {args.out_dir / 'round_level.csv'}")
    for message in validation_messages:
        print(message)
    if any(message.startswith("FAIL") for message in validation_messages):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
