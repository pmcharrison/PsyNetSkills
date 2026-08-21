import argparse
import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


STIMULI = [
    ("focus_positive", "normal", "focus_environment", "positive", None),
    ("focus_reversed", "normal", "focus_environment", "negative", None),
    ("planning_positive", "normal", "planning", "positive", None),
    ("planning_repeat", "normal", "planning", "positive", None),
    ("attention_check", "attention_check", None, "check", "2"),
    ("breaks_positive", "normal", "breaks", "positive", None),
]

STATEMENTS = {
    "focus_positive": "A quiet workspace makes it easier to concentrate.",
    "focus_reversed": "Background noise makes it easier to concentrate.",
    "planning_positive": "Making a simple plan before a task reduces mistakes.",
    "planning_repeat": "A short plan before starting work can reduce errors.",
    "attention_check": "Reading check: please select Mostly disagree for this item.",
    "breaks_positive": "Short breaks can help people maintain attention.",
}

PROFILES = {
    "P001": {
        "label": "mock_human_like",
        "description": "Varied responses, adequate latencies, passes the check.",
        "responses": {
            "focus_positive": "4",
            "focus_reversed": "2",
            "planning_positive": "5",
            "planning_repeat": "4",
            "attention_check": "2",
            "breaks_positive": "4",
        },
        "latencies_ms": [4200, 5100, 3900, 4700, 3600, 4500],
    },
    "P002": {
        "label": "mock_fast_uniform",
        "description": "Very fast straight-line responses.",
        "responses": {trial_id: "3" for trial_id, *_ in STIMULI},
        "latencies_ms": [210, 230, 205, 215, 225, 220],
    },
    "P003": {
        "label": "mock_attention_fail",
        "description": "Plausible speed but fails the embedded check.",
        "responses": {
            "focus_positive": "4",
            "focus_reversed": "2",
            "planning_positive": "4",
            "planning_repeat": "5",
            "attention_check": "5",
            "breaks_positive": "4",
        },
        "latencies_ms": [3400, 3600, 3150, 4100, 3000, 3900],
    },
    "P004": {
        "label": "mock_inconsistent_pair",
        "description": "Adequate speed but gives inconsistent related-item answers.",
        "responses": {
            "focus_positive": "5",
            "focus_reversed": "5",
            "planning_positive": "1",
            "planning_repeat": "5",
            "attention_check": "2",
            "breaks_positive": "4",
        },
        "latencies_ms": [2800, 2950, 3100, 3000, 3300, 3400],
    },
    "P005": {
        "label": "mock_missing_telemetry",
        "description": "Responses are present, but timing fields are missing.",
        "responses": {
            "focus_positive": "4",
            "focus_reversed": "2",
            "planning_positive": "4",
            "planning_repeat": "4",
            "attention_check": "2",
            "breaks_positive": "4",
        },
        "latencies_ms": [None, None, None, None, None, None],
    },
}


def default_evidence_dir():
    return Path(__file__).resolve().parents[2] / "evidence"


def build_export():
    base_time = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)
    trial_rows = []
    participants = []

    for participant_index, (participant_id, profile) in enumerate(PROFILES.items(), start=1):
        participants.append(
            {
                "participant_id": participant_id,
                "status": "simulated_local_complete",
                "local_profile_label": profile["label"],
                "local_profile_description": profile["description"],
                "source": "local_simulation_only",
            }
        )
        participant_start = base_time + timedelta(minutes=participant_index * 3)

        for trial_index, stimulus in enumerate(STIMULI):
            trial_id, item_type, pair_id, polarity, expected = stimulus
            latency_ms = profile["latencies_ms"][trial_index]
            trial_start = participant_start + timedelta(seconds=trial_index * 8)
            submit_time = (
                trial_start + timedelta(milliseconds=latency_ms)
                if latency_ms is not None
                else None
            )
            response = profile["responses"][trial_id]
            metadata = {
                "telemetry_version": "2026-06-11",
                "participant_id": participant_id,
                "local_profile_label": profile["label"],
                "local_profile_source": "simulated_profile",
                "trial_id": trial_id,
                "trial_position": trial_index,
                "item_type": item_type,
                "statement": STATEMENTS[trial_id],
                "pair_id": pair_id,
                "polarity": polarity,
                "response": response,
                "expected_response": expected,
                "attention_correct": None if expected is None else response == expected,
                "client_trial_start_time": iso_or_none(trial_start if latency_ms is not None else None),
                "client_response_submit_time": iso_or_none(submit_time),
                "response_latency_ms": latency_ms,
                "server_received_at": iso_or_none(
                    submit_time + timedelta(milliseconds=40) if submit_time else None
                ),
            }
            trial_rows.append(
                {
                    "trial_db_id": len(trial_rows) + 1,
                    "participant_id": participant_id,
                    "trial_id": trial_id,
                    "item_type": item_type,
                    "statement": STATEMENTS[trial_id],
                    "pair_id": pair_id,
                    "polarity": polarity,
                    "answer": response,
                    "score": 1.0 if expected is None or response == expected else 0.0,
                    "time_taken": None if latency_ms is None else latency_ms / 1000,
                    "response_metadata": metadata,
                }
            )

    return {
        "schema": "simulated_psynet_basic_data_v1",
        "source_note": (
            "Local simulated PsyNet-shaped export for challenge evidence only; "
            "no real participant or recruitment data are included."
        ),
        "participants": participants,
        "trial": trial_rows,
    }


def iso_or_none(value):
    return None if value is None else value.isoformat()


def write_outputs(evidence_dir):
    evidence_dir.mkdir(parents=True, exist_ok=True)
    export = build_export()
    json_path = evidence_dir / "simulated_psynet_export.json"
    csv_path = evidence_dir / "simulated_psynet_trial_rows.csv"
    zip_path = evidence_dir / "data.zip"

    json_path.write_text(json.dumps(export, indent=2), encoding="utf-8")
    write_trial_csv(export["trial"], csv_path)

    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(json_path, arcname=json_path.name)
        archive.write(csv_path, arcname=csv_path.name)

    return json_path, csv_path, zip_path


def write_trial_csv(rows, path):
    fieldnames = [
        "trial_db_id",
        "participant_id",
        "trial_id",
        "item_type",
        "pair_id",
        "polarity",
        "answer",
        "score",
        "time_taken",
        "response_latency_ms",
        "attention_correct",
        "local_profile_label",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            metadata = row["response_metadata"]
            writer.writerow(
                {
                    **{key: row.get(key) for key in fieldnames},
                    "response_latency_ms": metadata.get("response_latency_ms"),
                    "attention_correct": metadata.get("attention_correct"),
                    "local_profile_label": metadata.get("local_profile_label"),
                }
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path, default=default_evidence_dir())
    args = parser.parse_args()
    paths = write_outputs(args.evidence_dir)
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
