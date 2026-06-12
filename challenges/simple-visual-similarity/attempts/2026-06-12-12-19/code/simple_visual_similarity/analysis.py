"""Summarize simple visual similarity data as rating and reaction-time heatmaps."""

from __future__ import annotations

import argparse
import ast
import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean

STIMULI_PATH = Path(__file__).with_name("stimuli.json")


def list_stimuli() -> list[dict]:
    with STIMULI_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def parse_literal(value):
    if isinstance(value, (dict, list)):
        return value
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    for parser in (json.loads, ast.literal_eval):
        try:
            return parser(text)
        except Exception:
            pass
    return text


def load_rows(input_path: Path) -> list[dict]:
    files = []
    if input_path.is_dir():
        files.extend(sorted(input_path.glob("*.csv")))
        files.extend(sorted(input_path.glob("*.jsonl")))
        files.extend(sorted(input_path.glob("*.json")))
    else:
        files.append(input_path)

    rows = []
    for path in files:
        if path.suffix == ".csv":
            with path.open(newline="", encoding="utf-8") as f:
                rows.extend(csv.DictReader(f))
        elif path.suffix == ".jsonl":
            with path.open(encoding="utf-8") as f:
                rows.extend(json.loads(line) for line in f if line.strip())
        elif path.suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                rows.extend(payload)
            elif isinstance(payload, dict):
                for value in payload.values():
                    if isinstance(value, list):
                        rows.extend(value)
    return rows


def row_to_trial(row: dict) -> dict | None:
    definition = parse_literal(row.get("definition") or row.get("trial_definition"))
    if not isinstance(definition, dict) or "stimulus_a" not in definition:
        return None
    answer = parse_literal(row.get("answer") or row.get("trial_answer"))
    try:
        rating = float(answer)
    except (TypeError, ValueError):
        return None
    rt = row.get("time_taken") or row.get("reaction_time") or row.get("rt")
    try:
        reaction_time = float(rt) if rt not in (None, "") else None
    except (TypeError, ValueError):
        reaction_time = None
    return {
        "stimulus_a": definition["stimulus_a"]["stimulus_id"],
        "stimulus_b": definition["stimulus_b"]["stimulus_id"],
        "rating": rating,
        "reaction_time": reaction_time,
    }


def make_demo_trials(seed: int = 1) -> list[dict]:
    rng = random.Random(seed)
    stimuli = list_stimuli()
    trials = []
    for i, stimulus_a in enumerate(stimuli):
        for j, stimulus_b in enumerate(stimuli[i:], start=i):
            distance = abs(i - j)
            rating = max(1, 5 - min(distance, 4))
            trials.append(
                {
                    "stimulus_a": stimulus_a["stimulus_id"],
                    "stimulus_b": stimulus_b["stimulus_id"],
                    "rating": rating + rng.choice([-0.25, 0, 0.25]),
                    "reaction_time": round(0.65 + 0.12 * distance + rng.random() * 0.25, 3),
                }
            )
    return trials


def aggregate_matrix(trials: list[dict], value_key: str, stimuli: list[str]) -> list[list[float | None]]:
    grouped = defaultdict(list)
    for trial in trials:
        value = trial.get(value_key)
        if value is None:
            continue
        a = trial["stimulus_a"]
        b = trial["stimulus_b"]
        grouped[(a, b)].append(float(value))
        grouped[(b, a)].append(float(value))
    matrix = []
    for a in stimuli:
        row = []
        for b in stimuli:
            values = grouped.get((a, b), [])
            row.append(round(mean(values), 3) if values else None)
        matrix.append(row)
    return matrix


def write_matrix(path: Path, stimuli: list[str], matrix: list[list[float | None]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["stimulus"] + stimuli)
        for stimulus, row in zip(stimuli, matrix):
            writer.writerow([stimulus] + row)


def write_html_heatmap(path: Path, title: str, stimuli: list[str], matrix: list[list[float | None]], low: str, high: str) -> None:
    values = [value for row in matrix for value in row if value is not None]
    min_value = min(values) if values else 0
    max_value = max(values) if values else 1

    def color(value):
        if value is None:
            return "#f2f2f2"
        scale = 0 if max_value == min_value else (value - min_value) / (max_value - min_value)
        lo = tuple(int(low[i:i + 2], 16) for i in (1, 3, 5))
        hi = tuple(int(high[i:i + 2], 16) for i in (1, 3, 5))
        rgb = tuple(round(lo[i] + scale * (hi[i] - lo[i])) for i in range(3))
        return "#%02x%02x%02x" % rgb

    rows = []
    rows.append("<table><thead><tr><th></th>" + "".join(f"<th>{s}</th>" for s in stimuli) + "</tr></thead><tbody>")
    for stimulus, row in zip(stimuli, matrix):
        cells = [f"<th>{stimulus}</th>"]
        for value in row:
            text = "" if value is None else f"{value:.2f}"
            cells.append(f"<td style='background:{color(value)}'>{text}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    rows.append("</tbody></table>")
    path.write_text(
        "<!doctype html><meta charset='utf-8'><style>body{font-family:sans-serif}table{border-collapse:collapse}th,td{border:1px solid #bbb;padding:0.45rem;text-align:center}td{min-width:4rem}</style>"
        f"<h1>{title}</h1>" + "\n".join(rows),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="CSV/JSON/JSONL file or directory exported from PsyNet.")
    parser.add_argument("--output-dir", type=Path, default=Path("analysis_outputs"))
    parser.add_argument("--demo", action="store_true", help="Use deterministic demo data when exported/simulated data is unavailable.")
    args = parser.parse_args()

    if args.demo:
        trials = make_demo_trials()
    elif args.input:
        trials = [trial for row in load_rows(args.input) if (trial := row_to_trial(row))]
    else:
        raise SystemExit("Provide --input with exported/simulated data, or use --demo for deterministic example data.")

    if not trials:
        raise SystemExit("No visual similarity trial rows found.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stimuli = [stimulus["stimulus_id"] for stimulus in list_stimuli()]
    rating_matrix = aggregate_matrix(trials, "rating", stimuli)
    rt_matrix = aggregate_matrix(trials, "reaction_time", stimuli)
    write_matrix(args.output_dir / "similarity_rating_heatmap.csv", stimuli, rating_matrix)
    write_matrix(args.output_dir / "reaction_time_heatmap.csv", stimuli, rt_matrix)
    write_html_heatmap(args.output_dir / "similarity_rating_heatmap.html", "Mean similarity rating", stimuli, rating_matrix, "#f7fbff", "#08306b")
    write_html_heatmap(args.output_dir / "reaction_time_heatmap.html", "Mean reaction time", stimuli, rt_matrix, "#fff7ec", "#7f0000")
    summary = {
        "n_trials": len(trials),
        "stimuli": stimuli,
        "outputs": [
            "similarity_rating_heatmap.csv",
            "reaction_time_heatmap.csv",
            "similarity_rating_heatmap.html",
            "reaction_time_heatmap.html",
        ],
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
