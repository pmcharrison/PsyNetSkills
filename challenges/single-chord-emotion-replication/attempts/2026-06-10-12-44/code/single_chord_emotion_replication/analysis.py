from __future__ import annotations

    import argparse
    import json
    import zipfile
    from pathlib import Path

    import numpy as np
    import pandas as pd

    from .questionnaires import scale_names
    from .simulate_data import main as simulate_data
    from .synthesize_stimuli import main as synthesize_stimuli

    MANIFEST_PATH = Path(__file__).resolve().parent / "generated_stimuli" / "stimulus_manifest.json"


    def cronbach_alpha(frame: pd.DataFrame) -> float:
        items = frame.to_numpy(dtype=float)
        item_variances = items.var(axis=0, ddof=1)
        total_variance = items.sum(axis=1).var(ddof=1)
        if total_variance == 0.0:
            return 0.0
        n_items = items.shape[1]
        return float((n_items / (n_items - 1.0)) * (1.0 - item_variances.sum() / total_variance))


    def load_simulated_dataset(input_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        participants = pd.read_csv(input_path / "participants.csv")
        trials = pd.read_csv(input_path / "trial_ratings.csv")
        features = pd.read_csv(input_path / "stimulus_features.csv")
        return participants, trials, features


    def load_psynet_export(input_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
        if input_path.is_dir():
            trial_csv = input_path / "regular" / "basic_data" / "trial.csv"
            participant_csv = input_path / "regular" / "basic_data" / "participant.csv"
            if not trial_csv.exists():
                trial_csv = input_path / "trial.csv"
                participant_csv = input_path / "participant.csv"
            participants = pd.read_csv(participant_csv)
            trials = pd.read_csv(trial_csv)
            return participants, trials

        with zipfile.ZipFile(input_path, "r") as archive:
            trial_name = next(name for name in archive.namelist() if name.endswith("basic_data/trial.csv") or name.endswith("data/trial.csv"))
            participant_name = next(name for name in archive.namelist() if name.endswith("basic_data/participant.csv") or name.endswith("data/participant.csv"))
            with archive.open(participant_name) as participant_handle:
                participants = pd.read_csv(participant_handle)
            with archive.open(trial_name) as trial_handle:
                trials = pd.read_csv(trial_handle)
        return participants, trials


    def normalize_trial_frame(trials: pd.DataFrame) -> pd.DataFrame:
        if "answer" in trials.columns and "stimulus_id" not in trials.columns:
            answers = trials["answer"].apply(json.loads)
            normalized = pd.json_normalize(answers)
            keep_columns = [column for column in ["participant_id", "stimulus_id", "family", "inversion", "timbre"] if column in trials.columns]
            normalized = pd.concat([trials[keep_columns].reset_index(drop=True), normalized], axis=1)
            return normalized
        return trials.copy()


    def aggregate_report(participants: pd.DataFrame, trials: pd.DataFrame, features: pd.DataFrame) -> dict[str, object]:
        summary_by_family = (
            trials.groupby("family")[scale_names()]
            .mean()
            .round(3)
            .sort_index()
            .reset_index()
            .to_dict(orient="records")
        )
        summary_by_timbre = (
            trials.groupby("timbre")[["nostalgia_longing", "melancholy_sadness", "tenderness", "happiness_joy"]]
            .mean()
            .round(3)
            .sort_index()
            .reset_index()
            .to_dict(orient="records")
        )
        participant_dimension_means = trials.groupby("participant_id")[scale_names()].mean()
        reliability = {
            dimension: round(cronbach_alpha(trials.pivot(index="participant_id", columns="stimulus_id", values=dimension)), 3)
            for dimension in scale_names()
        }
        dimensional_correlations = participant_dimension_means.corr().round(3).to_dict()
        feature_means = trials.groupby("stimulus_id")[["nostalgia_longing", "tenderness"]].mean().reset_index()
        joined = feature_means.merge(features, on="stimulus_id", how="left")
        feature_correlations = (
            joined[["nostalgia_longing", "tenderness", "brightness", "roughness", "spectral_flux", "log_attack_time"]]
            .corr()
            .round(3)
            .to_dict()
        )
        return {
            "n_participants": int(participants.shape[0]),
            "n_trials": int(trials.shape[0]),
            "summary_by_family": summary_by_family,
            "summary_by_timbre": summary_by_timbre,
            "reliability": reliability,
            "dimension_correlations": dimensional_correlations,
            "feature_correlations": feature_correlations,
        }


    def write_report(report: dict[str, object], output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "analysis_summary.json").write_text(json.dumps(report, indent=2) + "
", encoding="ascii")
        lines = [
            "# Single chord emotion replication analysis",
            "",
            f"- Participants: {report['n_participants']}",
            f"- Trials: {report['n_trials']}",
            "",
            "## Mean ratings by chord family",
            "",
        ]
        for row in report["summary_by_family"]:
            lines.append(f"- {row['family']}: valence={row['valence']}, tension={row['tension']}, nostalgia={row['nostalgia_longing']}, happiness={row['happiness_joy']}")
        lines.extend([
            "",
            "## Timbre contrasts",
            "",
        ])
        for row in report["summary_by_timbre"]:
            lines.append(
                f"- {row['timbre']}: nostalgia={row['nostalgia_longing']}, melancholy={row['melancholy_sadness']}, tenderness={row['tenderness']}, happiness={row['happiness_joy']}"
            )
        lines.extend([
            "",
            "## Reliability",
            "",
        ])
        for key, value in report["reliability"].items():
            lines.append(f"- {key}: alpha={value}")
        (output_dir / "analysis_report.md").write_text("
".join(lines) + "
", encoding="ascii")


    def main(input_path: str | Path, output_dir: str | Path = "analysis_outputs") -> Path:
        if not MANIFEST_PATH.exists():
            synthesize_stimuli()
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        if (input_path / "participants.csv").exists():
            participants, trials, features = load_simulated_dataset(input_path)
        else:
            participants, trials = load_psynet_export(input_path)
            features = pd.DataFrame(json.loads(MANIFEST_PATH.read_text(encoding="ascii")))
            feature_columns = [
                {
                    "stimulus_id": item["stimulus_id"],
                    **item["features"],
                }
                for item in json.loads(MANIFEST_PATH.read_text(encoding="ascii"))
            ]
            features = pd.DataFrame(feature_columns)
        normalized_trials = normalize_trial_frame(trials)
        report = aggregate_report(participants, normalized_trials, features)
        write_report(report, output_dir)
        return output_dir


    if __name__ == "__main__":
        parser = argparse.ArgumentParser()
        parser.add_argument("--input", default="simulated_data")
        parser.add_argument("--output-dir", default="analysis_outputs")
        parser.add_argument("--simulate-if-missing", action="store_true")
        args = parser.parse_args()
        input_path = Path(args.input)
        if args.simulate_if_missing and not input_path.exists():
            simulate_data(input_path)
        result = main(input_path, args.output_dir)
        print(f"Wrote analysis outputs to {result}")
