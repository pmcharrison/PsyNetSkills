import argparse
from pathlib import Path

import pandas as pd


def simulate_task_data():
    stimuli = ["S1", "S2", "S3", "S4", "S5", "S6"]
    rows = []
    for left in stimuli:
        for right in stimuli:
            if left > right:
                continue
            rows.append(
                {
                    "block_name": "similarity_judgment",
                    "trial_kind": "similarity",
                    "left_id": left,
                    "right_id": right,
                    "answer": 6 if left == right else 3,
                    "accuracy": 1.0,
                    "reaction_time": 1.2,
                }
            )
    for index, stimulus in enumerate(stimuli):
        rows.append(
            {
                "block_name": "same_different_discrimination",
                "trial_kind": "discrimination",
                "left_id": stimulus,
                "right_id": stimulus,
                "condition": "same",
                "answer": "same",
                "accuracy": 1.0,
                "reaction_time": 0.9 + index * 0.02,
            }
        )
    for set_size in [3, 4, 5]:
        for probe_present in [True, False]:
            for response in range(1, set_size + 1):
                rows.append(
                    {
                        "block_name": "multi_item_identification",
                        "trial_kind": "identification",
                        "set_size": set_size,
                        "probe_id": stimuli[(response + set_size) % len(stimuli)],
                        "probe_present": probe_present,
                        "answer": str(response),
                        "correct_item_number": "1",
                        "accuracy": 1.0 if response == 1 else 0.0,
                        "reaction_time": 1.5 + 0.05 * response,
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


def load_task_data(input_path):
    if input_path is None:
        return simulate_task_data()
    return pd.read_csv(find_task_trial_csv(input_path))


def summarize_similarity(data):
    similarity = data[data["trial_kind"] == "similarity"].copy()
    similarity["rating"] = pd.to_numeric(similarity["answer"])
    matrix = similarity.pivot_table(
        index="left_id",
        columns="right_id",
        values="rating",
        aggfunc="mean",
    )
    for left_id in list(matrix.index):
        for right_id in list(matrix.columns):
            if pd.isna(matrix.loc[left_id, right_id]) and right_id in matrix.index and left_id in matrix.columns:
                matrix.loc[left_id, right_id] = matrix.loc[right_id, left_id]
    return matrix.sort_index().sort_index(axis=1)


def summarize_discrimination(data):
    discrimination = data[data["trial_kind"] == "discrimination"].copy()
    return (
        discrimination.groupby("condition", dropna=False)
        .agg(
            n_trials=("accuracy", "size"),
            mean_accuracy=("accuracy", "mean"),
            median_reaction_time=("reaction_time", "median"),
        )
        .reset_index()
    )


def summarize_identification(data):
    identification = data[data["trial_kind"] == "identification"].copy()
    confusion = pd.crosstab(
        [
            identification["set_size"],
            identification["probe_present"],
            identification["probe_id"],
        ],
        identification["answer"],
        normalize="index",
    )
    return confusion.reset_index()


def summarize_reaction_times(data):
    return (
        data.groupby("block_name", dropna=False)
        .agg(
            n_trials=("reaction_time", "size"),
            median_reaction_time=("reaction_time", "median"),
            mean_reaction_time=("reaction_time", "mean"),
        )
        .reset_index()
    )


def run_analysis(input_path, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data = load_task_data(input_path)
    outputs = {
        "similarity_matrix.csv": summarize_similarity(data),
        "discrimination_summary.csv": summarize_discrimination(data),
        "identification_confusion.csv": summarize_identification(data),
        "reaction_time_summary.csv": summarize_reaction_times(data),
    }
    for filename, table in outputs.items():
        table.to_csv(output_dir / filename, index=True)
    return outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Export directory or task_trial CSV path.")
    parser.add_argument("--output", default="analysis_output")
    args = parser.parse_args()
    outputs = run_analysis(args.input, args.output)
    for filename, table in outputs.items():
        print(f"\n{filename}")
        print(table)


if __name__ == "__main__":
    main()
