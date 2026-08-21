import argparse
import json
from pathlib import Path

import pandas as pd

from experiment import (
    STIMULI,
    hue_distance,
    identification_definitions,
    same_different_definitions,
    similarity_definitions,
    stimulus,
)


def simulate_dataset():
    rows = []
    for definition in same_different_definitions():
        rows.append(
            {
                **flatten(definition),
                "answer": definition["correct_answer"],
                "score": 1,
                "reaction_time": 1.1 + 0.03 * len(rows),
            }
        )
    for definition in similarity_definitions():
        rating = max(0, min(6, round(6 - definition["hue_distance"] / 30)))
        rows.append(
            {
                **flatten(definition),
                "answer": rating,
                "score": 1,
                "reaction_time": 1.4 + 0.02 * len(rows),
            }
        )
    for definition in identification_definitions():
        rows.append(
            {
                **flatten(definition),
                "answer": definition["nearest_item_number"],
                "score": 1,
                "reaction_time": 1.7 + 0.04 * len(rows),
            }
        )
    return pd.DataFrame.from_records(rows)


def flatten(definition):
    row = {}
    for key, value in definition.items():
        if isinstance(value, (dict, list)):
            row[key] = json.dumps(value, sort_keys=True)
        else:
            row[key] = value
    return row


def load_data(path):
    if path is None:
        return simulate_dataset()
    path = Path(path)
    if path.is_dir():
        candidates = sorted(path.rglob("trial.csv"))
        if not candidates:
            candidates = sorted(path.rglob("*trial*.csv"))
        if not candidates:
            raise FileNotFoundError(f"No trial CSV found under {path}")
        path = candidates[0]
    return pd.read_csv(path)


def similarity_matrix(df):
    stimuli = [stimulus["id"] for stimulus in STIMULI]
    matrix = pd.DataFrame(index=stimuli, columns=stimuli, dtype=float)
    sim = df[df["block"] == "similarity"].copy()
    for _, row in sim.iterrows():
        pair = json.loads(row["pair_identity"])
        rating = float(row["answer"])
        matrix.loc[pair[0], pair[1]] = rating
        matrix.loc[pair[1], pair[0]] = rating
    return matrix


def same_different_summary(df):
    sd = df[df["block"] == "same_different"].copy()
    return (
        sd.groupby("is_same")
        .agg(n=("trial_id", "count"), accuracy=("score", "mean"), mean_rt=("reaction_time", "mean"))
        .reset_index()
    )


def identification_confusions(df):
    ident = df[df["block"] == "identification"].copy()
    if ident.empty:
        return pd.DataFrame()
    ident["probe_id"] = ident["probe_stimulus"].apply(lambda value: json.loads(value)["id"])
    return (
        ident.groupby(["probe_id", "set_size", "probe_present", "answer"])
        .size()
        .rename("n")
        .reset_index()
        .assign(probability=lambda data: data["n"] / data.groupby(["probe_id", "set_size", "probe_present"])["n"].transform("sum"))
    )


def rt_summary(df):
    return (
        df.groupby("block")["reaction_time"]
        .describe(percentiles=[0.1, 0.5, 0.9])
        .reset_index()
    )


def stimulus_distances():
    rows = []
    for stim_a in STIMULI:
        for stim_b in STIMULI:
            rows.append(
                {
                    "stimulus_a": stim_a["id"],
                    "stimulus_b": stim_b["id"],
                    "hue_distance": hue_distance(stimulus(stim_a["id"]), stimulus(stim_b["id"])),
                }
            )
    return pd.DataFrame.from_records(rows)


def main():
    parser = argparse.ArgumentParser(description="Summarize similarity, discrimination, and identification data.")
    parser.add_argument("--input", help="Optional exported data directory or trial CSV. If omitted, uses simulated data.")
    parser.add_argument("--output", default="analysis_outputs", help="Directory for analysis summaries.")
    args = parser.parse_args()

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    df = load_data(args.input)

    similarity_matrix(df).to_csv(output / "similarity_matrix.csv")
    same_different_summary(df).to_csv(output / "same_different_summary.csv", index=False)
    identification_confusions(df).to_csv(output / "identification_confusions.csv", index=False)
    rt_summary(df).to_csv(output / "reaction_time_summary.csv", index=False)
    stimulus_distances().to_csv(output / "stimulus_distances.csv", index=False)

    summary = {
        "n_trials": int(len(df)),
        "blocks": sorted(df["block"].unique().tolist()),
        "input": args.input or "simulated deterministic dataset",
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
