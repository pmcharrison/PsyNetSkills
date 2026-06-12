from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


GROUP_FIELDS = [
    "prime_affect",
    "coded_target_response",
    "congruency",
    "prime_cultural_group",
    "target_cultural_group",
]


def load_records(path: Path) -> list[dict]:
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    raise ValueError("Expected .json or .jsonl input")


def summarize(records: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for record in records:
        key = tuple(record[field] for field in GROUP_FIELDS)
        groups[key].append(record)

    rows = []
    for key, values in sorted(groups.items()):
        happy = sum(1 for value in values if value["selected_response"] == "happy")
        rts = [
            value["response_time_from_target_ms"]
            for value in values
            if value.get("response_time_from_target_ms") is not None
        ]
        rows.append(
            {
                **dict(zip(GROUP_FIELDS, key)),
                "n": len(values),
                "p_happy": round(happy / len(values), 3),
                "mean_response_time_from_target_ms": round(sum(rts) / len(rts), 1) if rts else "",
                "note": "Workflow validation only; placeholder/bot data are not scientific evidence.",
            }
        )
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = GROUP_FIELDS + ["n", "p_happy", "mean_response_time_from_target_ms", "note"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    records = load_records(args.input)
    rows = summarize(records)
    write_csv(rows, args.output)
    print(f"Wrote {len(rows)} summary rows to {args.output}.")


if __name__ == "__main__":
    main()
