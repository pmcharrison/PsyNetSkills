#!/usr/bin/env python3
import argparse
import csv
import json
import statistics
import zipfile
from pathlib import Path


def find_member(zip_file, suffix):
    matches = [name for name in zip_file.namelist() if name.endswith(suffix)]
    if not matches:
        raise FileNotFoundError(f"Could not find {suffix} in {zip_file.filename}")
    regular = [name for name in matches if "/regular/" in f"/{name}"]
    return sorted(regular or matches)[0]


def read_csv_from_export(export_path, suffix):
    path = Path(export_path)
    if path.is_file() and path.suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            member = find_member(zf, suffix)
            with zf.open(member) as file:
                return list(csv.DictReader(line.decode("utf-8") for line in file))
    matches = sorted(path.rglob(suffix.lstrip("/")))
    if not matches:
        raise FileNotFoundError(f"Could not find {suffix} under {path}")
    with matches[0].open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def summarize(export_path):
    trials = read_csv_from_export(export_path, "basic_data/trial.csv")
    participants = read_csv_from_export(export_path, "basic_data/participant.csv")
    by_condition = {}
    for row in trials:
        condition = row["condition"]
        rating = float(row["curiosity_rating"])
        by_condition.setdefault(condition, []).append(rating)

    condition_summaries = {}
    for condition, ratings in sorted(by_condition.items()):
        condition_summaries[condition] = {
            "n_trials": len(ratings),
            "mean_curiosity_rating": round(statistics.mean(ratings), 3),
            "min_curiosity_rating": min(ratings),
            "max_curiosity_rating": max(ratings),
        }

    return {
        "participant_count": len({row["id"] for row in participants}),
        "trial_count": len(trials),
        "conditions": condition_summaries,
        "source": str(export_path),
    }


def main():
    parser = argparse.ArgumentParser(description="Summarize curiosity ratings from a PsyNet export.")
    parser.add_argument("export_path", help="Path to exported data directory or zip file.")
    parser.add_argument("--output", default=None, help="Optional JSON output path.")
    args = parser.parse_args()

    result = summarize(args.export_path)
    text = json.dumps(result, indent=2)
    print(text)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
