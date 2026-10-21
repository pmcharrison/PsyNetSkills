import argparse
import csv
import json
import zipfile
from pathlib import Path
from statistics import mean


SIMULATED_TRIALS = [
    {
        "current_state": {"tempo": 108, "brightness": 0.35},
        "proposal": {"tempo": 120, "brightness": 0.47},
        "answer": {"role": "proposal", "value": {"tempo": 120, "brightness": 0.47}},
    },
    {
        "current_state": {"tempo": 120, "brightness": 0.47},
        "proposal": {"tempo": 132, "brightness": 0.59},
        "answer": {"role": "proposal", "value": {"tempo": 132, "brightness": 0.59}},
    },
    {
        "current_state": {"tempo": 132, "brightness": 0.59},
        "proposal": {"tempo": 126, "brightness": 0.71},
        "answer": {"role": "proposal", "value": {"tempo": 126, "brightness": 0.71}},
    },
]


def load_trials(path):
    if path is None:
        return SIMULATED_TRIALS

    path = Path(path)
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            csv_name = next(
                (
                    name
                    for name in names
                    if name.endswith("PreferenceTrial.csv")
                    or name.endswith("db/info.csv")
                )
            )
            with archive.open(csv_name) as raw:
                return parse_info_csv(line.decode("utf-8") for line in raw)
    if path.suffix == ".csv":
        return parse_info_csv(path.read_text().splitlines())
    return json.loads(path.read_text())


def parse_info_csv(lines):
    trials = []
    for row in csv.DictReader(lines):
        answer = parse_json_field(row.get("answer") or row.get("details"))
        definition = parse_json_field(row.get("definition"))
        current_state = parse_json_field(row.get("current_state"))
        proposal = parse_json_field(row.get("proposal"))
        if not definition and current_state and proposal:
            definition = {"current_state": current_state, "proposal": proposal}
        if not answer and row.get("value"):
            answer = {
                "position": int(row["position"]),
                "role": row["role"],
                "value": parse_json_field(row["value"]),
            }
        if not answer or not definition or "current_state" not in definition:
            continue
        trials.append(
            {
                "current_state": definition["current_state"],
                "proposal": definition["proposal"],
                "answer": answer,
            }
        )
    return trials


def parse_json_field(value):
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def summarize(trials):
    choices = [trial["answer"]["value"] for trial in trials if trial.get("answer")]
    proposals_accepted = sum(
        1 for trial in trials if trial.get("answer", {}).get("role") == "proposal"
    )
    return {
        "n_trials": len(trials),
        "n_choices": len(choices),
        "proposals_accepted": proposals_accepted,
        "mean_chosen_tempo": round(mean(item["tempo"] for item in choices), 2),
        "mean_chosen_brightness": round(
            mean(item["brightness"] for item in choices), 3
        ),
        "final_choice": choices[-1] if choices else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input",
        nargs="?",
        help="Optional data.zip, db/info.csv, or JSON trial export. Uses simulated data if omitted.",
    )
    parser.add_argument("--output", default="analysis_summary.json")
    args = parser.parse_args()

    summary = summarize(load_trials(args.input))
    Path(args.output).write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
