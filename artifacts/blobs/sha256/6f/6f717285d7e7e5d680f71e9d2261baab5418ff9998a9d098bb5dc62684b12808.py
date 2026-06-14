import csv
import json
import math
import random
from pathlib import Path


SHAPE_SIZE = 400
SHAPES = [
    "circle",
    "triangle",
    "square",
    "vertical_oval",
    "horizontal_oval",
    "pentagon",
]


def prototypes(shape):
    if shape in {"circle", "vertical_oval", "horizontal_oval"}:
        return [(120, 120), (280, 120), (120, 280), (280, 280)]
    if shape == "triangle":
        return [(190, 80), (210, 80), (90, 310), (120, 330), (280, 330), (310, 310)]
    if shape == "square":
        return [(100, 100), (300, 100), (100, 300), (300, 300)]
    return [(200, 80), (310, 165), (270, 310), (130, 310), (90, 165)]


def nearest(point, candidates):
    return min(candidates, key=lambda p: (p[0] - point[0]) ** 2 + (p[1] - point[1]) ** 2)


def simulate(seed=2026, chains_per_shape=24, generations=10):
    random.seed(seed)
    rows = []
    for shape in SHAPES:
        targets = prototypes(shape)
        for chain in range(chains_per_shape):
            x = random.uniform(50, 350)
            y = random.uniform(50, 350)
            for generation in range(generations + 1):
                rows.append(
                    {
                        "shape": shape,
                        "seed_id": f"{shape}_{chain:03d}",
                        "generation": generation,
                        "response_x": round(x, 3),
                        "response_y": round(y, 3),
                    }
                )
                px, py = nearest((x, y), targets)
                pull = 0.28
                x = (1 - pull) * x + pull * px + random.gauss(0, 13)
                y = (1 - pull) * y + pull * py + random.gauss(0, 13)
                x = min(max(x, 0), SHAPE_SIZE)
                y = min(max(y, 0), SHAPE_SIZE)
    return rows


def histogram(rows, shape, generation, bins=25):
    grid = [[0.0 for _ in range(bins)] for _ in range(bins)]
    selected = [
        r
        for r in rows
        if r["shape"] == shape and int(r["generation"]) == generation
    ]
    for row in selected:
        ix = min(bins - 1, int(float(row["response_x"]) / SHAPE_SIZE * bins))
        iy = min(bins - 1, int(float(row["response_y"]) / SHAPE_SIZE * bins))
        grid[iy][ix] += 1.0

    # Simple Gaussian smoothing approximates a 2D kernel density estimate.
    smoothed = [[0.0 for _ in range(bins)] for _ in range(bins)]
    sigma = 1.2
    radius = 3
    for y in range(bins):
        for x in range(bins):
            total = 0.0
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < bins and 0 <= xx < bins:
                        weight = math.exp(-(dx * dx + dy * dy) / (2 * sigma * sigma))
                        total += grid[yy][xx] * weight
            smoothed[y][x] = total
    flat = [v for row in smoothed for v in row]
    mass = sum(flat) or 1.0
    return [v / mass for v in flat]


def js_divergence(p, q):
    def kl(a, b):
        return sum(ai * math.log2(ai / bi) for ai, bi in zip(a, b) if ai > 0 and bi > 0)

    m = [(pi + qi) / 2 for pi, qi in zip(p, q)]
    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def main():
    out_dir = Path("analysis_output")
    out_dir.mkdir(exist_ok=True)
    rows = simulate()

    csv_path = out_dir / "simulated_trials.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["shape", "seed_id", "generation", "response_x", "response_y"]
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = {}
    for shape in SHAPES:
        divergences = []
        for generation in range(10):
            p = histogram(rows, shape, generation)
            q = histogram(rows, shape, generation + 1)
            divergences.append(js_divergence(p, q))
        summary[shape] = {
            "successive_generation_jsd": [round(x, 5) for x in divergences],
            "final_generation_n": sum(
                1
                for r in rows
                if r["shape"] == shape and int(r["generation"]) == 10
            ),
        }

    summary_path = out_dir / "convergence_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Wrote {csv_path}")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
