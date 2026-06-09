"""Summarize exported STEP candidates from a PsyNet data export zip."""

from __future__ import annotations

import csv
import json
import sys
import zipfile
from pathlib import Path


def read_csv_from_zip(zip_path: Path, suffix: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(zip_path) as archive:
        matches = [name for name in archive.namelist() if name.endswith(suffix)]
        if not matches:
            return []
        with archive.open(matches[0]) as handle:
            text = handle.read().decode("utf-8")
    return list(csv.DictReader(text.splitlines()))


def parse_jsonish(value: str):
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def summarize(zip_path: Path) -> dict[str, object]:
    trial_rows = read_csv_from_zip(zip_path, "trial.csv")
    summary: dict[str, object] = {
        "zip_path": str(zip_path),
        "n_trials": len(trial_rows),
        "stimuli": {},
    }

    stimuli: dict[str, dict[str, object]] = summary["stimuli"]  # type: ignore[assignment]
    for row in trial_rows:
        answer = parse_jsonish(row.get("answer", ""))
        if not isinstance(answer, dict):
            continue
        candidates = answer.get("candidates", [])
        if not isinstance(candidates, list):
            continue
        stimulus_name = answer.get("name") or row.get("origin_id") or "unknown"
        stimulus_summary = stimuli.setdefault(
            str(stimulus_name),
            {
                "n_trials_with_answers": 0,
                "tags": {},
            },
        )
        stimulus_summary["n_trials_with_answers"] += 1  # type: ignore[index,operator]
        tags = stimulus_summary["tags"]  # type: ignore[index]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            text = str(candidate.get("text", ""))
            ratings = candidate.get("previous_ratings", [])
            tags[text] = {
                "ratings": ratings,
                "n_flags": sum(1 for rating in ratings if rating == 0),
                "is_flagged": candidate.get("is_flagged"),
                "is_frozen": candidate.get("is_frozen"),
                "is_new": candidate.get("is_new"),
            }

    return summary


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python scripts/summarize_step_export.py data.zip summary.json")
    summary = summarize(Path(sys.argv[1]))
    Path(sys.argv[2]).write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
