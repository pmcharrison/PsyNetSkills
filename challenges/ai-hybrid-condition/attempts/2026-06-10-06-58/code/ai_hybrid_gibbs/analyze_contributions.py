import argparse
import csv
import io
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

GOLDEN_RATIO_CONJUGATE = 0.6180339887498949


def choose_response_source(participant_id, ai_share):
    if ai_share <= 0:
        return "human"
    if ai_share >= 1:
        return "ai"
    low_discrepancy_position = (participant_id * GOLDEN_RATIO_CONJUGATE) % 1
    return "ai" if low_discrepancy_position < ai_share else "human"


def simulate_records(participants, trials_per_participant, ai_share):
    records = []
    for participant_id in range(1, participants + 1):
        response_source = choose_response_source(participant_id, ai_share)
        for trial_index in range(1, trials_per_participant + 1):
            records.append(
                {
                    "participant_id": participant_id,
                    "trial_id": f"{participant_id}-{trial_index}",
                    "response_source": response_source,
                    "ai_share": ai_share,
                }
            )
    return records


def rows_from_csv_text(text):
    return list(csv.DictReader(io.StringIO(text)))


def rows_from_json_text(text):
    data = json.loads(text)
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        for key in ["records", "rows", "data", "trials", "participants"]:
            value = data.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
        return [data]
    return []


def load_rows(path):
    path = Path(path)
    if path.suffix == ".zip":
        rows = []
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                suffix = Path(name).suffix
                if suffix not in {".csv", ".json", ".jsonl"}:
                    continue
                text = archive.read(name).decode("utf-8")
                for row in parse_text_rows(text, suffix):
                    row["__source_file"] = name
                    rows.append(row)
        return rows
    rows = parse_text_rows(path.read_text(encoding="utf-8"), path.suffix)
    for row in rows:
        row["__source_file"] = path.name
    return rows


def parse_text_rows(text, suffix):
    if suffix == ".csv":
        return rows_from_csv_text(text)
    if suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    if suffix == ".json":
        return rows_from_json_text(text)
    raise ValueError(f"Unsupported input suffix: {suffix}")


def value_from_details(row, key):
    for details_key in ["details", "vars", "var", "metadata"]:
        value = row.get(details_key)
        if not value:
            continue
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                continue
        if isinstance(value, dict) and key in value:
            return value[key]
    return None


def field(row, key):
    return row.get(key) or value_from_details(row, key)


def trial_id_from_row(row):
    if field(row, "trial_id"):
        return field(row, "trial_id")
    source_file = str(row.get("__source_file", "")).lower()
    if "trial" in source_file and row.get("id"):
        return row["id"]
    return None


def summarize(records):
    participant_sources = {}
    trial_counts = Counter()
    trial_counts_by_participant = defaultdict(Counter)

    for row in records:
        response_source = field(row, "response_source")
        if response_source not in {"human", "ai"}:
            continue
        participant_id = str(field(row, "participant_id") or field(row, "participant") or "")
        trial_id = trial_id_from_row(row)

        if participant_id:
            participant_sources.setdefault(participant_id, response_source)
            trial_counts_by_participant[participant_id][response_source] += 1
        if trial_id is not None:
            trial_counts[response_source] += 1

    participant_counts = Counter(participant_sources.values())
    total_participants = sum(participant_counts.values())
    total_trials = sum(trial_counts.values())

    return {
        "participants": {
            "total": total_participants,
            "human": participant_counts["human"],
            "ai": participant_counts["ai"],
            "ai_share_observed": (
                participant_counts["ai"] / total_participants
                if total_participants
                else None
            ),
        },
        "trials": {
            "total": total_trials,
            "human": trial_counts["human"],
            "ai": trial_counts["ai"],
            "ai_share_observed": trial_counts["ai"] / total_trials if total_trials else None,
        },
        "trials_by_participant": {
            participant_id: dict(counts)
            for participant_id, counts in sorted(trial_counts_by_participant.items())
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="CSV, JSON, JSONL, or data.zip export to inspect.")
    parser.add_argument("--simulate", action="store_true", help="Generate simulated records.")
    parser.add_argument("--participants", type=int, default=12)
    parser.add_argument("--trials-per-participant", type=int, default=7)
    parser.add_argument("--ai-share", type=float, default=0.5)
    parser.add_argument("--json-output", help="Optional path to write the summary JSON.")
    args = parser.parse_args()

    if args.input:
        records = load_rows(args.input)
    else:
        records = simulate_records(
            participants=args.participants,
            trials_per_participant=args.trials_per_participant,
            ai_share=args.ai_share,
        )

    summary = summarize(records)
    text = json.dumps(summary, indent=2, sort_keys=True)
    print(text)
    if args.json_output:
        Path(args.json_output).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
