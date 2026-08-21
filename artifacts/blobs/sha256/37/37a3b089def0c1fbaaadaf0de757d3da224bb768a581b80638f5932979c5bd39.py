import argparse
from pathlib import Path

import pandas as pd


def simulated_data():
    stimuli = [f"S{i}" for i in range(1, 7)]
    rows = []
    for i, left in enumerate(stimuli):
        for right in stimuli[i:]:
            rows.append(
                {
                    "block_name": "similarity_judgment",
                    "trial_kind": "similarity",
                    "left_id": left,
                    "right_id": right,
                    "answer": 6 if left == right else 3,
                    "accuracy": 1.0,
                    "reaction_time": 0.8,
                }
            )
    for i, left in enumerate(stimuli):
        rows.append(
            {
                "block_name": "same_different_discrimination",
                "trial_kind": "discrimination",
                "left_id": left,
                "right_id": left,
                "condition": "same",
                "answer": "same",
                "accuracy": 1.0,
                "reaction_time": 0.7 + i * 0.01,
            }
        )
        rows.append(
            {
                "block_name": "same_different_discrimination",
                "trial_kind": "discrimination",
                "left_id": left,
                "right_id": stimuli[(i + 1) % len(stimuli)],
                "condition": "different",
                "answer": "different",
                "accuracy": 1.0,
                "reaction_time": 0.8 + i * 0.01,
            }
        )
    for set_size in [3, 4, 5]:
        for probe_present in [True, False]:
            for answer in range(1, set_size + 1):
                rows.append(
                    {
                        "block_name": "multi_item_identification",
                        "trial_kind": "identification",
                        "set_size": set_size,
                        "probe_id": stimuli[(answer + set_size) % len(stimuli)],
                        "probe_present": probe_present,
                        "answer": str(answer),
                        "correct_item_number": "1",
                        "accuracy": 1.0 if answer == 1 else 0.0,
                        "reaction_time": 1.0 + answer * 0.02,
                    }
                )
    return pd.DataFrame.from_records(rows)


def find_task_trial_csv(path):
    path = Path(path)
    if path.is_file():
        return path
    matches = sorted(path.rglob("task_trial.csv"))
    if not matches:
        matches = sorted(path.rglob("*task_trial*.csv"))
    if not matches:
        raise FileNotFoundError(f"Could not find task_trial CSV under {path}")
    return matches[0]


def load_data(input_path):
    if input_path is None:
        return simulated_data()
    return pd.read_csv(find_task_trial_csv(input_path))


def similarity_matrix(data):
    ratings = data[data["trial_kind"] == "similarity"].copy()
    ratings["rating"] = pd.to_numeric(ratings["answer"])
    matrix = ratings.pivot_table(
        index="left_id",
        columns="right_id",
        values="rating",
        aggfunc="mean",
    )
    for left in list(matrix.index):
        for right in list(matrix.columns):
            if pd.isna(matrix.loc[left, right]) and right in matrix.index and left in matrix.columns:
                matrix.loc[left, right] = matrix.loc[right, left]
    return matrix.sort_index().sort_index(axis=1)


def discrimination_summary(data):
    trials = data[data["trial_kind"] == "discrimination"]
    return (
        trials.groupby("condition", dropna=False)
        .agg(
            n_trials=("accuracy", "size"),
            mean_accuracy=("accuracy", "mean"),
            median_reaction_time=("reaction_time", "median"),
        )
        .reset_index()
    )


def identification_confusion(data):
    trials = data[data["trial_kind"] == "identification"]
    return pd.crosstab(
        [trials["set_size"], trials["probe_present"], trials["probe_id"]],
        trials["answer"],
        normalize="index",
    ).reset_index()


def reaction_times(data):
    return (
        data.groupby("block_name", dropna=False)
        .agg(
            n_trials=("reaction_time", "size"),
            median_reaction_time=("reaction_time", "median"),
            mean_reaction_time=("reaction_time", "mean"),
        )
        .reset_index()
    )


def run(input_path, output_dir):
    data = load_data(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "similarity_matrix.csv": similarity_matrix(data),
        "discrimination_summary.csv": discrimination_summary(data),
        "identification_confusion.csv": identification_confusion(data),
        "reaction_time_summary.csv": reaction_times(data),
    }
    for name, table in outputs.items():
        table.to_csv(output_dir / name, index=True)
    return outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Export directory or task_trial CSV path.")
    parser.add_argument("--output", default="analysis_output")
    args = parser.parse_args()
    for name, table in run(args.input, args.output).items():
        print(f"\n{name}")
        print(table)


if __name__ == "__main__":
    main()
