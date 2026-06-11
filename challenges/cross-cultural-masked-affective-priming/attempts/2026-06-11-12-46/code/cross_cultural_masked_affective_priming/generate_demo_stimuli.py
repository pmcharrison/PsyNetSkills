from __future__ import annotations

import json
from pathlib import Path

STIMULUS_DIR = Path("data/stimuli")
MANIFEST_PATH = Path("data/manifest.json")

TIMINGS_MS = {
    "fixation": 500,
    "forward_mask": 100,
    "prime": 50,
    "backward_mask": 100,
    "target_display": 3000,
    "inter_trial": 250,
}


def face_svg(label: str, affect: str, group: str, ambiguity: float = 0.0) -> str:
    if affect == "happy":
        mouth = "M 70 122 Q 100 150 130 122"
        brow = "M 65 75 Q 78 67 91 75 M 109 75 Q 122 67 135 75"
        accent = "#f7c948"
    elif affect == "angry":
        mouth = "M 70 140 Q 100 116 130 140"
        brow = "M 62 69 L 91 82 M 109 82 L 138 69"
        accent = "#e05243"
    else:
        mouth = f"M 70 {132 - ambiguity:.1f} Q 100 {130 + ambiguity:.1f} 130 {132 - ambiguity:.1f}"
        brow = "M 65 75 Q 78 70 91 75 M 109 75 Q 122 70 135 75"
        accent = "#7aa6c2"

    skin = "#f2c6a0" if group == "demo_a" else "#b9855f"
    bg = "#e8f4ff" if group == "demo_a" else "#f4ecff"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="320" height="240" viewBox="0 0 200 180" role="img" aria-label="{label}">
  <rect width="200" height="180" fill="{bg}"/>
  <circle cx="100" cy="88" r="58" fill="{skin}" stroke="#343434" stroke-width="3"/>
  <path d="{brow}" fill="none" stroke="#343434" stroke-width="5" stroke-linecap="round"/>
  <circle cx="78" cy="92" r="7" fill="#222"/>
  <circle cx="122" cy="92" r="7" fill="#222"/>
  <path d="{mouth}" fill="none" stroke="#343434" stroke-width="6" stroke-linecap="round"/>
  <circle cx="166" cy="28" r="14" fill="{accent}" opacity="0.85"/>
</svg>
"""


def mask_svg() -> str:
    squares = []
    colors = ["#202124", "#f1f3f4", "#9aa0a6", "#5f6368"]
    for y in range(0, 180, 20):
        for x in range(0, 200, 20):
            color = colors[(x // 20 + y // 20) % len(colors)]
            squares.append(f'<rect x="{x}" y="{y}" width="20" height="20" fill="{color}"/>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="320" height="240" viewBox="0 0 200 180" role="img" aria-label="visual mask">
  {''.join(squares)}
</svg>
"""


def write_assets() -> None:
    STIMULUS_DIR.mkdir(parents=True, exist_ok=True)
    (STIMULUS_DIR / "mask_checker.svg").write_text(mask_svg(), encoding="utf-8")

    for group in ["demo_a", "demo_b"]:
        for affect in ["happy", "angry"]:
            path = STIMULUS_DIR / f"prime_{affect}_{group}.svg"
            path.write_text(face_svg(path.stem, affect, group), encoding="utf-8")

        for response, ambiguity in [("happy", 8.0), ("angry", -8.0)]:
            path = STIMULUS_DIR / f"target_ambiguous_{response}_{group}.svg"
            path.write_text(
                face_svg(path.stem, "ambiguous", group, ambiguity=ambiguity),
                encoding="utf-8",
            )


def make_trial(
    block: str,
    trial_index: int,
    prime_affect: str,
    prime_group: str,
    target_response: str,
    target_group: str,
) -> dict:
    congruency = "congruent" if prime_affect == target_response else "incongruent"
    return {
        "trial_id": f"{block}_{trial_index:02d}_{prime_affect}_{prime_group}_{target_response}_{target_group}",
        "block": block,
        "prime_id": f"prime_{prime_affect}_{prime_group}",
        "prime_affect": prime_affect,
        "prime_cultural_group": prime_group,
        "target_id": f"target_ambiguous_{target_response}_{target_group}",
        "target_ambiguity": "60-40 demonstration morph",
        "target_cultural_group": target_group,
        "coded_target_response": target_response,
        "mask_id": "mask_checker",
        "congruency": congruency,
        "timings_ms": TIMINGS_MS,
        "stimulus_note": "Generated placeholder; replace with validated face stimuli for real research.",
    }


def write_manifest() -> None:
    practice = [
        make_trial("practice", 1, "happy", "demo_a", "happy", "demo_a"),
        make_trial("practice", 2, "angry", "demo_b", "angry", "demo_b"),
    ]
    main = []
    i = 1
    for prime_group, target_group in [
        ("demo_a", "demo_a"),
        ("demo_a", "demo_b"),
        ("demo_b", "demo_a"),
        ("demo_b", "demo_b"),
    ]:
        main.append(make_trial("main", i, "happy", prime_group, "happy", target_group))
        i += 1
        main.append(make_trial("main", i, "angry", prime_group, "happy", target_group))
        i += 1

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps({"timings_ms": TIMINGS_MS, "trials": practice + main}, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    write_assets()
    write_manifest()
    print(f"Wrote {MANIFEST_PATH} and SVG stimuli under {STIMULUS_DIR}.")
