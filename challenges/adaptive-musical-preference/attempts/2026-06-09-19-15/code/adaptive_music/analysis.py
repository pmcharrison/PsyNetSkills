import argparse
import csv
import json
import random
import zipfile
from collections import Counter
from pathlib import Path

TEMPOS = [84, 96, 108, 120, 132, 144]
BRIGHTNESSES = [1, 2, 3, 4, 5]


def utility(stimulus):
    return -(abs(stimulus["tempo"] - 120) / 12 + 0.8 * abs(stimulus["brightness"] - 4))


def clamp(value, values):
    return min(max(value, min(values)), max(values))


def proposal(state):
    candidates = []
    for tempo_step in [-24, -12, 0, 12, 24]:
        for brightness_step in [-1, 0, 1]:
            if tempo_step == 0 and brightness_step == 0:
                continue
            candidate = {
                "tempo": clamp(state["tempo"] + tempo_step, TEMPOS),
                "brightness": clamp(state["brightness"] + brightness_step, BRIGHTNESSES),
            }
            if candidate != state and candidate not in candidates:
                candidates.append(candidate)
    return random.choice(candidates)


def simulate(n_trials=12):
    state = {"tempo": 84, "brightness": 1}
    rows = []
    for trial_index in range(n_trials):
        proposed = proposal(state)
        chosen = proposed if utility(proposed) >= utility(state) else state
        rows.append(
            {
                "trial_index": trial_index,
                "current_state": state,
                "proposal": proposed,
                "choice": chosen,
            }
        )
        state = chosen
    return rows


def parse_jsonish(value):
    if not value:
        return None
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def load_from_export(path):
    rows = []
    with zipfile.ZipFile(path) as archive:
        candidates = [
            name
            for name in archive.namelist()
            if name.endswith("PreferenceTrial.csv") or name.endswith("info.csv")
        ]
        if not candidates:
            return rows
        trial_table = sorted(
            candidates, key=lambda name: not name.endswith("PreferenceTrial.csv")
        )[0]
        with archive.open(trial_table) as raw:
            reader = csv.DictReader(line.decode("utf-8") for line in raw)
            for row in reader:
                if row.get("complete") not in {None, "", "True", "true", "1"}:
                    continue
                definition = parse_jsonish(row.get("definition"))
                answer = parse_jsonish(row.get("answer") or row.get("details"))
                if not definition or not answer or "current_state" not in definition:
                    continue
                rows.append(
                    {
                        "trial_index": len(rows),
                        "current_state": definition["current_state"],
                        "proposal": definition["proposal"],
                        "choice": answer.get("value", answer),
                    }
                )
    return rows


def summarize(rows):
    choices = [row["choice"] for row in rows]
    if not choices:
        return {"n_choices": 0}
    tempo_counts = Counter(choice["tempo"] for choice in choices)
    brightness_counts = Counter(choice["brightness"] for choice in choices)
    return {
        "n_choices": len(choices),
        "mean_tempo": sum(choice["tempo"] for choice in choices) / len(choices),
        "mean_brightness": sum(choice["brightness"] for choice in choices) / len(choices),
        "tempo_counts": dict(sorted(tempo_counts.items())),
        "brightness_counts": dict(sorted(brightness_counts.items())),
        "final_choice": choices[-1],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-zip", type=Path)
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.data_zip:
        rows = load_from_export(args.data_zip)
    elif args.simulate:
        rows = simulate()
    else:
        parser.error("Pass --data-zip or --simulate.")

    result = {"summary": summarize(rows), "trials": rows}
    text = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
