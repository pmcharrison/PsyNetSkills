import argparse
import json
import zipfile
from pathlib import Path

import pandas as pd


def load_stimuli():
    return json.loads(Path("stimuli.json").read_text())["stimuli"]


def color_distance(a, b):
    raw = abs(a - b)
    return min(raw, 360 - raw)


def simulate_trials():
    stimuli = load_stimuli()
    stimulus_ids = [stimulus["id"] for stimulus in stimuli]
    hues = {stimulus["id"]: stimulus["dimensions"]["hue_degrees"] for stimulus in stimuli}
    rows = []
    for left_index, left in enumerate(stimulus_ids):
        for right in stimulus_ids[left_index:]:
            distance = color_distance(hues[left], hues[right])
            rows.append(
                {
                    "task": "same_different",
                    "condition": "identical" if left == right else "different",
                    "left_id": left,
                    "right_id": right,
                    "answer": "same" if distance < 20 else "different",
                    "score": 1 if (left == right or distance >= 20) else 0,
                    "reaction_time_s": 0.8 + distance / 360,
                }
            )
            rows.append(
                {
                    "task": "similarity",
                    "condition": "rating",
                    "left_id": left,
                    "right_id": right,
                    "answer": round(max(0, 6 - distance / 45)),
                    "score": 1,
                    "reaction_time_s": 1.0 + distance / 300,
                }
            )
    for set_size in [3, 4, 5]:
        for probe_present in [True, False]:
            for probe_id in stimulus_ids:
                rows.append(
                    {
                        "task": "identification",
                        "condition": "probe_present" if probe_present else "probe_absent_lure",
                        "probe_id": probe_id,
                        "set_size": set_size,
                        "answer": 1,
                        "score": 1 if probe_present else int(probe_id in ["red", "orange", "yellow"]),
                        "reaction_time_s": 1.1 + 0.15 * set_size + (0 if probe_present else 0.25),
                    }
                )
    return pd.DataFrame.from_records(rows)


def load_export(path):
    path = Path(path)
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            candidates = [
                name
                for name in archive.namelist()
                if name.endswith(".csv") and "trial" in name.lower()
            ]
            if not candidates:
                raise ValueError("No trial CSV found in exported ZIP.")
            with archive.open(candidates[0]) as f:
                return pd.read_csv(f)
    return pd.read_csv(path)


def normalize_trials(df):
    if "definition" not in df.columns:
        return df
    records = []
    for _, row in df.iterrows():
        definition = json.loads(row["definition"].replace("'", '"')) if isinstance(row["definition"], str) else row["definition"]
        record = dict(row)
        if isinstance(definition, dict):
            if definition.get("task") in ["same_different", "similarity"]:
                record["left_id"], record["right_id"] = definition["stimulus_ids"]
            if definition.get("task") == "identification":
                record["probe_id"] = definition["probe_stimulus"]["id"]
                record["set_size"] = definition["set_size"]
            record["condition"] = definition.get("condition", record.get("condition"))
        records.append(record)
    return pd.DataFrame.from_records(records)


def write_outputs(df, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    similarity = df[df["task"] == "similarity"].copy()
    similarity["rating"] = pd.to_numeric(similarity["answer"])
    matrix = similarity.pivot_table(
        index="left_id",
        columns="right_id",
        values="rating",
        aggfunc="mean",
    )
    matrix.to_csv(output_dir / "similarity_matrix.csv")

    discrimination = (
        df[df["task"] == "same_different"]
        .groupby("condition")
        .agg(accuracy=("score", "mean"), mean_rt_s=("reaction_time_s", "mean"), n=("score", "size"))
    )
    discrimination.to_csv(output_dir / "discrimination_summary.csv")

    identification = df[df["task"] == "identification"].copy()
    identification["probe_present"] = identification["condition"].eq("probe_present")
    confusion = identification.pivot_table(
        index=["probe_id", "set_size", "probe_present"],
        values="score",
        aggfunc=["mean", "count"],
    )
    confusion.to_csv(output_dir / "identification_confusion.csv")

    rt_summary = (
        df.groupby("task")
        .agg(
            n=("reaction_time_s", "size"),
            mean_rt_s=("reaction_time_s", "mean"),
            median_rt_s=("reaction_time_s", "median"),
            p90_rt_s=("reaction_time_s", lambda x: x.quantile(0.9)),
        )
        .reset_index()
    )
    rt_summary.to_csv(output_dir / "reaction_time_summary.csv", index=False)

    report = output_dir / "README.md"
    report.write_text(
        "# Analysis outputs\n\n"
        "This directory was generated by `analysis.py`. If no export path is provided, "
        "the script uses a documented simulated dataset with one row per trial.\n\n"
        "- `similarity_matrix.csv`: mean 0-6 ratings by stimulus pair.\n"
        "- `discrimination_summary.csv`: same-different accuracy and reaction times.\n"
        "- `identification_confusion.csv`: nearest-item correctness by probe, set size, and probe presence.\n"
        "- `reaction_time_summary.csv`: reaction-time distributions by task block.\n"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Optional exported trial CSV or data ZIP.")
    parser.add_argument("--output", default="analysis_outputs")
    args = parser.parse_args()

    df = load_export(args.input) if args.input else simulate_trials()
    df = normalize_trials(df)
    write_outputs(df, Path(args.output))
    print(f"Wrote analysis outputs to {args.output}")


if __name__ == "__main__":
    main()
