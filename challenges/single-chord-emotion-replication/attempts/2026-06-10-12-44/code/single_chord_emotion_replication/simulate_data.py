from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .questionnaires import scale_names, score_omsi
    from .synthesize_stimuli import CHORD_SPECS, TIMBRE_SPECS, main as synthesize_stimuli
except ImportError:
    from questionnaires import scale_names, score_omsi
    from synthesize_stimuli import CHORD_SPECS, TIMBRE_SPECS, main as synthesize_stimuli

MANIFEST_PATH = Path(__file__).resolve().parent / "generated_stimuli" / "stimulus_manifest.json"

BASE_MEANS = {
    "major_triad": {
        "valence": 4.05,
        "tension": 2.60,
        "energy": 2.95,
        "nostalgia_longing": 2.05,
        "melancholy_sadness": 1.60,
        "interest_expectancy": 2.25,
        "happiness_joy": 3.35,
        "tenderness": 2.10,
        "liking_preference": 2.70,
    },
    "minor_triad": {
        "valence": 2.55,
        "tension": 3.05,
        "energy": 2.85,
        "nostalgia_longing": 2.90,
        "melancholy_sadness": 3.40,
        "interest_expectancy": 2.70,
        "happiness_joy": 1.85,
        "tenderness": 2.40,
        "liking_preference": 2.55,
    },
    "diminished_triad": {
        "valence": 2.10,
        "tension": 3.80,
        "energy": 3.35,
        "nostalgia_longing": 2.20,
        "melancholy_sadness": 3.05,
        "interest_expectancy": 3.40,
        "happiness_joy": 1.45,
        "tenderness": 1.90,
        "liking_preference": 2.05,
    },
    "augmented_triad": {
        "valence": 2.10,
        "tension": 4.00,
        "energy": 3.45,
        "nostalgia_longing": 2.10,
        "melancholy_sadness": 3.00,
        "interest_expectancy": 3.55,
        "happiness_joy": 1.35,
        "tenderness": 1.80,
        "liking_preference": 1.95,
    },
    "dominant_seventh": {
        "valence": 2.80,
        "tension": 3.45,
        "energy": 3.10,
        "nostalgia_longing": 2.70,
        "melancholy_sadness": 2.50,
        "interest_expectancy": 3.55,
        "happiness_joy": 2.35,
        "tenderness": 2.20,
        "liking_preference": 2.75,
    },
    "minor_seventh": {
        "valence": 2.85,
        "tension": 3.05,
        "energy": 2.85,
        "nostalgia_longing": 2.85,
        "melancholy_sadness": 2.65,
        "interest_expectancy": 3.00,
        "happiness_joy": 2.00,
        "tenderness": 2.65,
        "liking_preference": 3.00,
    },
    "major_seventh": {
        "valence": 2.95,
        "tension": 3.20,
        "energy": 2.95,
        "nostalgia_longing": 2.90,
        "melancholy_sadness": 2.55,
        "interest_expectancy": 3.10,
        "happiness_joy": 1.95,
        "tenderness": 2.55,
        "liking_preference": 3.05,
    },
}

TIMBRE_SHIFT = {
    "piano": {
        "nostalgia_longing": -0.20,
        "melancholy_sadness": -0.18,
        "tenderness": -0.12,
        "happiness_joy": 0.10,
    },
    "strings": {
        "nostalgia_longing": 0.20,
        "melancholy_sadness": 0.18,
        "tenderness": 0.12,
        "happiness_joy": -0.10,
    },
}

INVERSION_SHIFT = {
    ("major_triad", "first"): {"valence": 0.18, "energy": 0.15, "tension": 0.18, "happiness_joy": 0.12, "liking_preference": 0.08},
    ("major_triad", "second"): {"valence": 0.28, "energy": 0.28, "tension": 0.34, "interest_expectancy": 0.18, "happiness_joy": 0.18, "liking_preference": 0.15},
    ("minor_triad", "first"): {"valence": 0.08, "energy": 0.10, "tension": 0.12, "interest_expectancy": 0.08},
    ("minor_triad", "second"): {"valence": 0.12, "energy": 0.16, "tension": 0.20, "interest_expectancy": 0.14, "liking_preference": 0.08},
    ("dominant_seventh", "third"): {"energy": -0.05, "tension": 0.06, "interest_expectancy": 0.05},
    ("minor_seventh", "third"): {"energy": -0.04, "tension": 0.05, "nostalgia_longing": 0.10},
    ("major_seventh", "third"): {"energy": -0.04, "tension": 0.07, "nostalgia_longing": 0.20, "liking_preference": 0.08},
}


def load_manifest() -> list[dict]:
    if not MANIFEST_PATH.exists():
        synthesize_stimuli()
    return json.loads(MANIFEST_PATH.read_text(encoding="ascii"))


def participant_rows(rng: np.random.Generator, n_participants: int) -> pd.DataFrame:
    rows = []
    for participant_id in range(1, n_participants + 1):
        age = int(rng.integers(18, 72))
        age_started = int(rng.choice([0] + list(range(4, 19))))
        private_lessons = int(max(0, rng.normal(4.5, 4.0)))
        regular_practice = int(max(0, rng.normal(4.0, 4.5)))
        practice_amount = rng.choice([
            "rarely_or_never",
            "one_hour_per_month",
            "one_hour_per_week",
            "fifteen_minutes_per_day",
            "one_hour_per_day",
            "more_than_two_hours_per_day",
        ], p=[0.20, 0.12, 0.22, 0.20, 0.17, 0.09])
        coursework = rng.choice([
            "none",
            "one_or_two_nonmajor_courses",
            "three_or_more_nonmajor_courses",
            "preparatory_program",
            "one_year_bmus",
            "two_years_bmus",
            "three_or_more_years_bmus",
            "bmus_degree",
            "graduate_level",
        ], p=[0.50, 0.12, 0.10, 0.05, 0.07, 0.05, 0.05, 0.04, 0.02])
        composition = rng.choice([
            "never",
            "bits_and_pieces",
            "completed_but_not_performed",
            "performed_in_educational_context",
            "performed_for_local_audience",
            "performed_for_regional_or_national_audience",
        ], p=[0.45, 0.20, 0.13, 0.12, 0.07, 0.03])
        concerts = rng.choice([
            "none",
            "one_to_four",
            "five_to_eight",
            "nine_to_twelve",
            "thirteen_or_more",
        ], p=[0.10, 0.38, 0.24, 0.16, 0.12])
        self_title = rng.choice([
            "nonmusician",
            "music_loving_nonmusician",
            "amateur_musician",
            "serious_amateur_musician",
            "semiprofessional_musician",
            "professional_musician",
        ], p=[0.18, 0.30, 0.22, 0.16, 0.08, 0.06])

        omsi = score_omsi(
            {
                "omsi_age": age,
                "omsi_age_started": age_started,
                "omsi_private_lessons_years": private_lessons,
                "omsi_regular_practice_years": regular_practice,
                "omsi_current_practice_amount": practice_amount,
                "omsi_college_coursework": coursework,
                "omsi_composition_experience": composition,
                "omsi_concert_attendance": concerts,
                "omsi_self_title": self_title,
            }
        )

        rows.append(
            {
                "participant_id": participant_id,
                "age": age,
                "gender": rng.choice(["female", "male"], p=[0.56, 0.44]),
                "nationality": rng.choice(["FI", "US", "NZ", "GB", "DE", "OTHER"], p=[0.46, 0.18, 0.08, 0.08, 0.06, 0.14]),
                "education": rng.choice(["bachelor", "master", "doctorate_or_professional", "some_college"], p=[0.30, 0.26, 0.16, 0.28]),
                "panas_positive": float(rng.normal(15.5, 3.0)),
                "panas_negative": float(rng.normal(10.5, 3.0)),
                "omsi_score": omsi["score"],
                "omsi_group": omsi["group"],
            }
        )
    return pd.DataFrame(rows)


def clip_rating(value: float) -> float:
    return float(min(5.0, max(1.0, value)))


def trial_rows(rng: np.random.Generator, participants: pd.DataFrame, manifest: list[dict]) -> pd.DataFrame:
    rows = []
    by_family = participants["omsi_score"].rank(pct=True).to_numpy()
    for participant_index, participant in participants.reset_index(drop=True).iterrows():
        participant_offset = rng.normal(0.0, 0.18, size=len(scale_names()))
        positive_shift = (participant["panas_positive"] - participants["panas_positive"].mean()) / 20.0
        negative_shift = (participant["panas_negative"] - participants["panas_negative"].mean()) / 20.0
        omsi_shift = (participant["omsi_score"] - participants["omsi_score"].mean()) / 1000.0
        shuffled = list(manifest)
        rng.shuffle(shuffled)
        for trial_index, stimulus in enumerate(shuffled, start=1):
            means = dict(BASE_MEANS[stimulus["family"]])
            means.update({key: means.get(key, 0.0) + value for key, value in TIMBRE_SHIFT[stimulus["timbre"]].items()})
            for key, value in INVERSION_SHIFT.get((stimulus["family"], stimulus["inversion"]), {}).items():
                means[key] = means.get(key, 0.0) + value

            ratings = {}
            for dim_index, dimension in enumerate(scale_names()):
                mean_value = means[dimension]
                if dimension in {"energy", "interest_expectancy", "liking_preference"}:
                    mean_value += 0.40 * omsi_shift
                if dimension in {"nostalgia_longing", "melancholy_sadness", "tenderness"}:
                    mean_value += 0.35 * negative_shift
                if dimension in {"energy", "interest_expectancy", "happiness_joy", "liking_preference"}:
                    mean_value += 0.35 * positive_shift
                noise = rng.normal(0.0, 0.42)
                ratings[dimension] = round(clip_rating(mean_value + participant_offset[dim_index] + noise), 3)

            rows.append(
                {
                    "participant_id": participant["participant_id"],
                    "trial_index": trial_index,
                    "stimulus_id": stimulus["stimulus_id"],
                    "family": stimulus["family"],
                    "inversion": stimulus["inversion"],
                    "timbre": stimulus["timbre"],
                    **ratings,
                }
            )
    return pd.DataFrame(rows)


def main(output_dir: str | Path = "simulated_data", n_participants: int = 269, seed: int = 13) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    manifest = load_manifest()
    participants = participant_rows(rng, n_participants)
    trials = trial_rows(rng, participants, manifest)
    stimulus_features = pd.DataFrame(
        [
            {
                "stimulus_id": item["stimulus_id"],
                "family": item["family"],
                "inversion": item["inversion"],
                "timbre": item["timbre"],
                **item["features"],
            }
            for item in manifest
        ]
    )
    participants.to_csv(output_dir / "participants.csv", index=False)
    trials.to_csv(output_dir / "trial_ratings.csv", index=False)
    stimulus_features.to_csv(output_dir / "stimulus_features.csv", index=False)
    metadata = {
        "n_participants": n_participants,
        "seed": seed,
        "n_trials": int(trials.shape[0]),
        "n_stimuli": len(manifest),
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="ascii")
    return output_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="simulated_data")
    parser.add_argument("--n-participants", type=int, default=269)
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()
    path = main(args.output_dir, args.n_participants, args.seed)
    print(f"Wrote simulated dataset to {path}")
