import argparse
import io
import json
import zipfile
from pathlib import Path

import pandas as pd


def read_trial_data(path):
    path = Path(path)
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            trial_name = next(
                name for name in archive.namelist() if name.endswith("trial.csv")
            )
            with archive.open(trial_name) as file:
                return pd.read_csv(file)
    return pd.read_csv(path)


def ensure_flat_columns(trials):
    if "selected_animal" in trials.columns:
        return trials

    if "answer" not in trials.columns:
        raise ValueError("Trial data must contain either selected_animal or answer.")

    parsed = trials["answer"].apply(json.loads).apply(pd.Series)
    return pd.concat([trials.drop(columns=["answer"]), parsed], axis=1)


def analyze(trial_data, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    trials = ensure_flat_columns(read_trial_data(trial_data))
    counts = (
        trials.groupby(["prompt_key", "locale", "selected_animal"])
        .size()
        .rename("n")
        .reset_index()
    )
    counts["proportion"] = counts["n"] / counts.groupby(["prompt_key", "locale"])[
        "n"
    ].transform("sum")

    summary_path = output_dir / "choice_proportions.csv"
    counts.to_csv(summary_path, index=False)

    try:
        import matplotlib.pyplot as plt

        plot_data = counts.pivot_table(
            index=["prompt_key", "locale"],
            columns="selected_animal",
            values="proportion",
            fill_value=0,
        )
        axes = plot_data.plot(kind="bar", ylim=(0, 1), ylabel="Choice proportion")
        axes.figure.tight_layout()
        axes.figure.savefig(output_dir / "choice_proportions.png", dpi=150)
        plt.close(axes.figure)
    except ImportError:
        pass

    return summary_path


def write_demo_data(path):
    rows = [
        {
            "prompt_key": "companion",
            "locale": "en",
            "selected_animal": "cat",
        },
        {
            "prompt_key": "community_respect",
            "locale": "en",
            "selected_animal": "dog",
        },
        {
            "prompt_key": "companion",
            "locale": "en",
            "selected_animal": "dog",
        },
        {
            "prompt_key": "community_respect",
            "locale": "en",
            "selected_animal": "bird",
        },
    ]
    data = pd.DataFrame.from_records(rows)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(path, index=False)
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trial-data", default=None)
    parser.add_argument("--output-dir", default="../../evidence/analyses")
    args = parser.parse_args()

    if args.trial_data is None:
        buffer = io.StringIO()
        demo_path = write_demo_data(Path(args.output_dir) / "demo_trial_data.csv")
        args.trial_data = str(demo_path)

    summary_path = analyze(args.trial_data, args.output_dir)
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
