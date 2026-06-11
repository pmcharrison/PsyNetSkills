import argparse
import json
import random
from collections import Counter, defaultdict
from itertools import combinations_with_replacement
from pathlib import Path
from statistics import mean, median

STIMULUS_PATH = Path(__file__).parent / "data" / "stimuli.json"


def load_stimuli():
    with open(STIMULUS_PATH, encoding="utf-8") as f:
        return json.load(f)


def hue_distance(a, b):
    delta = abs(a["dimensions"]["color"]["hue_degrees"] - b["dimensions"]["color"]["hue_degrees"])
    return min(delta, 360 - delta)


def simulated_trials(seed=42):
    rng = random.Random(seed)
    stimuli = load_stimuli()
    trials = []
    for a, b in combinations_with_replacement(stimuli, 2):
        distance = hue_distance(a, b)
        base_rating = max(0, min(6, round(6 * (1 - distance / 180))))
        trials.append(
            {
                "block": "similarity",
                "stimulus_a": a["stimulus_id"],
                "stimulus_b": b["stimulus_id"],
                "rating": max(0, min(6, base_rating + rng.choice([-1, 0, 0, 1]))),
                "reaction_time_sec": round(rng.uniform(0.7, 2.8), 3),
            }
        )
        same = a["stimulus_id"] == b["stimulus_id"]
        if same or rng.random() < 0.7:
            trials.append(
                {
                    "block": "same_different",
                    "stimulus_a": a["stimulus_id"],
                    "stimulus_b": b["stimulus_id"],
                    "is_identical": same,
                    "correct": rng.random() < (0.95 if same else 0.84),
                    "reaction_time_sec": round(rng.uniform(0.55, 2.2), 3),
                }
            )
    for set_size in [3, 4, 5]:
        for probe_present in [True, False]:
            for probe_index, probe in enumerate(stimuli):
                response = rng.randint(1, set_size)
                nearest = (probe_index % set_size) + 1
                if rng.random() < (0.82 if probe_present else 0.62):
                    response = nearest
                trials.append(
                    {
                        "block": "identification",
                        "set_size": set_size,
                        "probe_present": probe_present,
                        "probe_stimulus": probe["stimulus_id"],
                        "response": response,
                        "nearest_item_number": nearest,
                        "nearest_neighbor_correct": response == nearest,
                        "reaction_time_sec": round(rng.uniform(0.8, 3.4), 3),
                    }
                )
    return trials


def rt_summary(rows):
    values = [row["reaction_time_sec"] for row in rows if row.get("reaction_time_sec") is not None]
    if not values:
        return {"n": 0, "mean": None, "median": None, "min": None, "max": None}
    return {
        "n": len(values),
        "mean": round(mean(values), 4),
        "median": round(median(values), 4),
        "min": min(values),
        "max": max(values),
    }


def summarize(trials):
    stimuli = [stimulus["stimulus_id"] for stimulus in load_stimuli()]
    by_block = defaultdict(list)
    for trial in trials:
        by_block[trial["block"]].append(trial)

    matrix = {row: {col: None for col in stimuli} for row in stimuli}
    grouped_ratings = defaultdict(list)
    for trial in by_block["similarity"]:
        a = trial["stimulus_a"]
        b = trial["stimulus_b"]
        grouped_ratings[tuple(sorted([a, b]))].append(trial["rating"])
    for (a, b), ratings in grouped_ratings.items():
        value = round(mean(ratings), 3)
        matrix[a][b] = value
        matrix[b][a] = value

    discrimination = by_block["same_different"]
    discrimination_summary = {
        "n_trials": len(discrimination),
        "accuracy": round(mean([trial["correct"] for trial in discrimination]), 4),
        "accuracy_by_condition": {},
        "reaction_time_sec": rt_summary(discrimination),
    }
    for condition in [True, False]:
        subset = [trial for trial in discrimination if trial["is_identical"] == condition]
        discrimination_summary["accuracy_by_condition"]["same" if condition else "different"] = round(mean([trial["correct"] for trial in subset]), 4)

    confusion_counts = Counter()
    confusion_totals = Counter()
    for trial in by_block["identification"]:
        key = (trial["probe_stimulus"], trial["set_size"], trial["probe_present"], trial["response"])
        total_key = (trial["probe_stimulus"], trial["set_size"], trial["probe_present"])
        confusion_counts[key] += 1
        confusion_totals[total_key] += 1
    confusion_probabilities = []
    for (probe, set_size, probe_present, response), count in sorted(confusion_counts.items()):
        total = confusion_totals[(probe, set_size, probe_present)]
        confusion_probabilities.append(
            {
                "probe_stimulus": probe,
                "set_size": set_size,
                "probe_present": probe_present,
                "response": response,
                "probability": round(count / total, 4),
            }
        )

    return {
        "source": "documented simulated dataset generated by analysis.py",
        "similarity": {
            "n_trials": len(by_block["similarity"]),
            "matrix": matrix,
            "reaction_time_sec": rt_summary(by_block["similarity"]),
        },
        "same_different": discrimination_summary,
        "identification": {
            "n_trials": len(by_block["identification"]),
            "nearest_neighbor_accuracy": round(mean([trial["nearest_neighbor_correct"] for trial in by_block["identification"]]), 4),
            "confusion_probabilities": confusion_probabilities,
            "reaction_time_sec": rt_summary(by_block["identification"]),
        },
        "reaction_time_by_block_sec": {
            block: rt_summary(rows) for block, rows in sorted(by_block.items())
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="analysis-summary.json")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    summary = summarize(simulated_trials(seed=args.seed))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
