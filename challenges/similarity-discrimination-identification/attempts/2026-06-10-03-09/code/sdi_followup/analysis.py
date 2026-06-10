import argparse
import html
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


def write_svg(path, content, width=760, height=520):
    Path(path).write_text(
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' "
        f"viewBox='0 0 {width} {height}'>"
        "<style>text{font-family:Arial,sans-serif;font-size:13px}.title{font-size:18px;font-weight:bold}</style>"
        f"{content}</svg>\n",
        encoding="utf-8",
    )


def color_for_value(value, min_value, max_value):
    if pd.isna(value):
        return "#f0f0f0"
    span = max(max_value - min_value, 1e-9)
    ratio = max(0.0, min(1.0, (float(value) - min_value) / span))
    red = int(245 - 180 * ratio)
    green = int(245 - 75 * ratio)
    blue = int(245 - 25 * ratio)
    return f"#{red:02x}{green:02x}{blue:02x}"


def similarity_matrix_svg(matrix, path):
    labels = list(matrix.index)
    cell = 54
    left = 120
    top = 80
    values = [float(v) for v in matrix.to_numpy().flatten() if not pd.isna(v)]
    min_value = min(values) if values else 0
    max_value = max(values) if values else 6
    parts = ["<text class='title' x='30' y='35'>Similarity matrix</text>"]
    for i, row_label in enumerate(labels):
        parts.append(f"<text x='{left - 12}' y='{top + i * cell + 33}' text-anchor='end'>{html.escape(str(row_label))}</text>")
    for j, col_label in enumerate(matrix.columns):
        parts.append(f"<text x='{left + j * cell + 27}' y='{top - 12}' text-anchor='middle'>{html.escape(str(col_label))}</text>")
    for i, row_label in enumerate(labels):
        for j, col_label in enumerate(matrix.columns):
            value = matrix.loc[row_label, col_label]
            fill = color_for_value(value, min_value, max_value)
            x = left + j * cell
            y = top + i * cell
            label = "" if pd.isna(value) else f"{float(value):.1f}"
            parts.append(f"<rect x='{x}' y='{y}' width='{cell}' height='{cell}' fill='{fill}' stroke='#ffffff'/>")
            parts.append(f"<text x='{x + cell / 2}' y='{y + cell / 2 + 5}' text-anchor='middle'>{label}</text>")
    write_svg(path, "".join(parts), width=560, height=460)


def bar_chart_svg(table, label_col, value_col, title, path, width=760, height=420):
    table = table.copy()
    table[value_col] = pd.to_numeric(table[value_col], errors="coerce").fillna(0)
    max_value = max(float(table[value_col].max()), 1.0)
    left = 190
    top = 65
    bar_h = 30
    gap = 14
    plot_w = width - left - 80
    parts = [f"<text class='title' x='30' y='35'>{html.escape(title)}</text>"]
    for i, row in table.reset_index(drop=True).iterrows():
        y = top + i * (bar_h + gap)
        label = str(row[label_col])
        value = float(row[value_col])
        bar_w = plot_w * value / max_value
        parts.append(f"<text x='{left - 10}' y='{y + 21}' text-anchor='end'>{html.escape(label)}</text>")
        parts.append(f"<rect x='{left}' y='{y}' width='{bar_w:.1f}' height='{bar_h}' fill='#4575b4'/>")
        parts.append(f"<text x='{left + bar_w + 8}' y='{y + 21}'>{value:.2f}</text>")
    write_svg(path, "".join(parts), width=width, height=max(height, top + len(table) * (bar_h + gap) + 40))


def response_distribution(data):
    counts = (
        data.groupby(["block_name", "answer"], dropna=False)
        .size()
        .reset_index(name="n")
    )
    counts["label"] = counts["block_name"].astype(str) + " / " + counts["answer"].astype(str)
    return counts


def run(input_path, output_dir):
    data = load_data(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    sim_matrix = similarity_matrix(data)
    disc_summary = discrimination_summary(data)
    ident_confusion = identification_confusion(data)
    rt_summary = reaction_times(data)
    resp_dist = response_distribution(data)
    outputs = {
        "similarity_matrix.csv": sim_matrix,
        "discrimination_summary.csv": disc_summary,
        "identification_confusion.csv": ident_confusion,
        "reaction_time_summary.csv": rt_summary,
        "response_distribution.csv": resp_dist,
    }
    for name, table in outputs.items():
        table.to_csv(output_dir / name, index=True)
    similarity_matrix_svg(sim_matrix, output_dir / "similarity_matrix.svg")
    bar_chart_svg(resp_dist, "label", "n", "Response distributions", output_dir / "response_distribution.svg")
    bar_chart_svg(disc_summary, "condition", "mean_accuracy", "Discrimination accuracy", output_dir / "discrimination_accuracy.svg")
    rt_plot = rt_summary.rename(columns={"block_name": "label", "median_reaction_time": "median_rt"})
    bar_chart_svg(rt_plot, "label", "median_rt", "Median reaction times", output_dir / "reaction_time_summary.svg")
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
