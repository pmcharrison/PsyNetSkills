"""Run local simulated participant profiles and export PsyNet-style data files."""

from __future__ import annotations

import argparse
import csv
import json
import random
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from stimuli import PROFILE_DESCRIPTIONS, WORD_PAIRS, choices_for_trial, role_for_answer


N_PARTICIPANTS_PER_PROFILE = 3


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def prompt_for(trial, revised):
    warning = (
        "Remember: recent words from other pairs can be traps. "
        if revised
        else ""
    )
    return (
        f"{warning}Cue: {trial['cue']}. Choices: "
        + ", ".join(choices_for_trial(trial))
        + ". Return exactly one choice."
    )


def answer_for_profile(profile, trial, rng, revised):
    if profile == "psynet_bot_rule":
        return trial["target"]

    if profile == "scripted_noisy":
        target_probability = 0.58 if not revised else 0.62
        if rng.random() < target_probability:
            return trial["target"]
        return rng.choice(choices_for_trial(trial))

    if profile == "mock_llm_memory_limited":
        if trial["condition"] == "literal":
            return trial["target"] if rng.random() < 0.86 else trial["semantic_lure"]
        if revised:
            return trial["target"] if rng.random() < 0.68 else trial["recent_lure"]
        return trial["recent_lure"] if rng.random() < 0.72 else trial["target"]

    if profile == "semantic_bias":
        bias_probability = 0.48 if revised else 0.7
        if rng.random() < bias_probability:
            return trial["semantic_lure"]
        return trial["target"]

    raise ValueError(f"Unknown profile: {profile}")


def response_time_ms(profile, trial, rng):
    base = {
        "psynet_bot_rule": 900,
        "scripted_noisy": 2600,
        "mock_llm_memory_limited": 1800,
        "semantic_bias": 1500,
    }[profile]
    return base + trial["difficulty"] * 110 + rng.randint(-150, 250)


def simulate(run_id, revised, output_dir, seed):
    rng = random.Random(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    participants = []
    trials = []
    events = []
    metadata = {
        "run_id": run_id,
        "revision": "revised" if revised else "initial",
        "created_at": now_iso(),
        "seed": seed,
        "n_participants_per_profile": N_PARTICIPANTS_PER_PROFILE,
        "profiles": PROFILE_DESCRIPTIONS,
        "export_format": "PsyNet-style local simulation export",
    }

    trial_counter = 1
    for profile_index, profile in enumerate(PROFILE_DESCRIPTIONS):
        for repeat in range(N_PARTICIPANTS_PER_PROFILE):
            participant_id = f"{run_id}-P{profile_index + 1}{repeat + 1}"
            participants.append(
                {
                    "participant_id": participant_id,
                    "run_id": run_id,
                    "profile": profile,
                    "profile_description": PROFILE_DESCRIPTIONS[profile],
                    "simulator": "psynet_bot" if profile == "psynet_bot_rule" else "local_script",
                    "started_at": now_iso(),
                    "status": "approved",
                }
            )
            for position, trial in enumerate(WORD_PAIRS, start=1):
                answer = answer_for_profile(profile, trial, rng, revised)
                answer_role = role_for_answer(trial, answer)
                correct = answer == trial["target"]
                row = {
                    "trial_id": f"{run_id}-T{trial_counter:04d}",
                    "participant_id": participant_id,
                    "run_id": run_id,
                    "revision": "revised" if revised else "initial",
                    "profile": profile,
                    "position": position,
                    "pair_id": trial["pair_id"],
                    "condition": trial["condition"],
                    "cue": trial["cue"],
                    "target": trial["target"],
                    "semantic_lure": trial["semantic_lure"],
                    "recent_lure": trial["recent_lure"],
                    "neutral_lure": trial["neutral_lure"],
                    "answer": answer,
                    "answer_role": answer_role,
                    "correct": int(correct),
                    "response_time_ms": response_time_ms(profile, trial, rng),
                    "prompt": prompt_for(trial, revised),
                }
                trials.append(row)
                events.append(
                    {
                        "event": "trial_response",
                        "trial_id": row["trial_id"],
                        "participant_id": participant_id,
                        "profile": profile,
                        "condition": trial["condition"],
                        "answer_role": answer_role,
                        "correct": correct,
                    }
                )
                trial_counter += 1

    write_csv(output_dir / "participants.csv", participants)
    write_csv(output_dir / "trials.csv", trials)
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    with (output_dir / "events.jsonl").open("w") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")

    zip_path = output_dir.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output_dir.iterdir()):
            archive.write(path, arcname=f"{output_dir.name}/{path.name}")
    return zip_path


def write_csv(path, rows):
    if not rows:
        raise ValueError(f"No rows to write for {path}")
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--revised", action="store_true")
    args = parser.parse_args()

    zip_path = simulate(args.run_id, args.revised, args.output_dir, args.seed)
    print(f"Wrote {zip_path}")


if __name__ == "__main__":
    main()
