"""Generate the trial manifest for the audio memory sequence experiment."""

from __future__ import annotations

import json
from pathlib import Path

MANIFEST_PATH = Path(__file__).with_name("trials_manifest.json")

TRIALS = [
    {
        "trial_id": "practice",
        "target_sequence": ["low", "high"],
        "practice": True,
    },
    {
        "trial_id": 1,
        "target_sequence": ["low", "medium", "high"],
    },
    {
        "trial_id": 2,
        "target_sequence": ["high", "low", "medium"],
    },
    {
        "trial_id": 3,
        "target_sequence": ["medium", "high", "low", "medium"],
    },
    {
        "trial_id": 4,
        "target_sequence": ["low", "low", "high", "medium"],
    },
]


def main() -> None:
    """Write the committed trial manifest."""
    MANIFEST_PATH.write_text(
        json.dumps({"trials": TRIALS}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(TRIALS)} trials to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
