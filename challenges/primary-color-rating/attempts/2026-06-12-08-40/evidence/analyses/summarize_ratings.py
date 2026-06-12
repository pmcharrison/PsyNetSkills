"""Summarize simulated primary color rating data.

This script reads the PsyNet simulation export and writes small review artifacts
that summarize rating completeness and color-level pleasantness ratings.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
import zipfile
from collections import defaultdict
from pathlib import Path


COLOR_ORDER = ["red", "green", "blue"]


def read_trials(export_zip: Path) -> list[dict[str, str]]:
    """Read regular exported trial rows from a PsyNet simulation zip."""

    with zipfile.ZipFile(export_zip) as archive:
        with archive.open("regular/data/ColorRatingTrial.csv") as file:
            text = (line.decode("utf-8") for line in file)
            return list(csv.DictReader(text))


def completed_color_trials(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    """Return completed trial rows with normalized rating fields."""

    trials = []
    for row in rows:
        if row["failed"] == "True" or row["complete"] != "True":
            continue
        trials.append(
            {
                "participant_id": int(row["participant_id"]),
                "color": row["name"],
                "block_position": int(row["block_position"]),
                "rating": int(row["answer"]),
            }
        )
    return trials


def summarize_by_color(trials: list[dict[str, object]]) -> list[dict[str, object]]:
    """Compute descriptive statistics by color."""

    ratings_by_color: dict[str, list[int]] = defaultdict(list)
    for trial in trials:
        ratings_by_color[str(trial["color"])].append(int(trial["rating"]))

    summary = []
    for color in COLOR_ORDER:
        ratings = ratings_by_color[color]
        summary.append(
            {
                "color": color,
                "n": len(ratings),
                "mean": statistics.fmean(ratings),
                "median": statistics.median(ratings),
                "min": min(ratings),
                "max": max(ratings),
                "stdev": statistics.stdev(ratings) if len(ratings) > 1 else 0.0,
            }
        )
    return summary


def participant_matrix(trials: list[dict[str, object]]) -> dict[int, dict[str, int]]:
    """Return participant-by-color rating matrix."""

    matrix: dict[int, dict[str, int]] = defaultdict(dict)
    for trial in trials:
        matrix[int(trial["participant_id"])][str(trial["color"])] = int(trial["rating"])
    return dict(matrix)


def validate_completeness(matrix: dict[int, dict[str, int]]) -> None:
    """Assert that every simulated participant has one response per color."""

    for participant_id, ratings in matrix.items():
        if set(ratings) != set(COLOR_ORDER):
            raise ValueError(
                f"Participant {participant_id} has ratings for {sorted(ratings)}, "
                f"expected {COLOR_ORDER}."
            )


def friedman_test(matrix: dict[int, dict[str, int]]) -> dict[str, float | int]:
    """Compute a small-sample Friedman test summary.

    For this deterministic bot simulation, the p-value is a pipeline check rather
    than evidence about real human color preference.
    """

    n = len(matrix)
    k = len(COLOR_ORDER)
    rank_sums = {color: 0.0 for color in COLOR_ORDER}
    for ratings in matrix.values():
        sorted_colors = sorted(COLOR_ORDER, key=lambda color: ratings[color])
        for rank, color in enumerate(sorted_colors, start=1):
            rank_sums[color] += rank
    q = (12 / (n * k * (k + 1))) * sum(value**2 for value in rank_sums.values()) - (
        3 * n * (k + 1)
    )
    # For df=2, the chi-square survival function is exp(-x / 2).
    p_value = math.exp(-q / 2)
    return {
        "n_participants": n,
        "df": k - 1,
        "statistic": q,
        "p_value_chi_square_df2": p_value,
        "rank_sum_red": rank_sums["red"],
        "rank_sum_green": rank_sums["green"],
        "rank_sum_blue": rank_sums["blue"],
    }


def write_summary_csv(summary: list[dict[str, object]], output: Path) -> None:
    """Write color-level summary statistics."""

    with output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["color", "n", "mean", "median", "min", "max", "stdev"],
        )
        writer.writeheader()
        writer.writerows(summary)


def write_svg(summary: list[dict[str, object]], output: Path) -> None:
    """Write a small SVG bar chart of mean ratings by color."""

    width, height = 520, 320
    chart_left, chart_bottom = 70, 260
    chart_top = 30
    bar_width = 80
    gap = 55
    color_hex = {"red": "#ff0000", "green": "#00a000", "blue": "#0057ff"}
    bars = []
    for index, row in enumerate(summary):
        color = str(row["color"])
        mean = float(row["mean"])
        x = chart_left + index * (bar_width + gap)
        bar_height = (mean / 7.0) * (chart_bottom - chart_top)
        y = chart_bottom - bar_height
        bars.append(
            f'<rect x="{x}" y="{y:.1f}" width="{bar_width}" height="{bar_height:.1f}" '
            f'fill="{color_hex[color]}" rx="6" />'
        )
        bars.append(
            f'<text x="{x + bar_width / 2}" y="{chart_bottom + 24}" text-anchor="middle">{color}</text>'
        )
        bars.append(
            f'<text x="{x + bar_width / 2}" y="{y - 8:.1f}" text-anchor="middle">{mean:.1f}</text>'
        )

    output.write_text(
        "\n".join(
            [
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                '<rect width="100%" height="100%" fill="white" />',
                '<text x="20" y="22" font-family="sans-serif" font-size="16">Mean simulated pleasantness rating</text>',
                f'<line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_bottom}" stroke="#24292f" />',
                f'<line x1="{chart_left}" y1="{chart_bottom}" x2="{width - 50}" y2="{chart_bottom}" stroke="#24292f" />',
                '<text x="22" y="145" font-family="sans-serif" font-size="13" transform="rotate(-90 22 145)">Rating (1-7)</text>',
                *bars,
                "</svg>",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    """Run the simulation-data analysis."""

    analysis_dir = Path(__file__).resolve().parent
    evidence_dir = analysis_dir.parent
    export_zip = evidence_dir / "simulated_data.zip"
    trials = completed_color_trials(read_trials(export_zip))
    matrix = participant_matrix(trials)
    validate_completeness(matrix)

    summary = summarize_by_color(trials)
    test = friedman_test(matrix)
    result = {
        "source": str(export_zip.relative_to(evidence_dir)),
        "n_trials": len(trials),
        "n_participants": len(matrix),
        "expected_trials_per_participant": len(COLOR_ORDER),
        "summary": summary,
        "friedman_test": test,
        "interpretation": (
            "All simulated participants completed one red, one green, and one blue "
            "rating. Ratings reflect deterministic bot responses, so inferential "
            "statistics validate the analysis pipeline rather than human behavior."
        ),
    }

    write_summary_csv(summary, analysis_dir / "rating_summary.csv")
    (analysis_dir / "rating_summary.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    write_svg(summary, analysis_dir / "rating_means.svg")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
