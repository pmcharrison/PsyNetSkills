from __future__ import annotations

import argparse
import json
from pathlib import Path

from signals import PROFILE_LABELS, build_synthetic_telemetry, utc_now


HERE = Path(__file__).parent
STIMULI = json.loads((HERE / "stimuli.json").read_text(encoding="utf-8"))


PROFILE_NOTES = {
    "attentive_human_like": "Careful responses, checks passed, no paste or focus events.",
    "inattentive": "Distracted local mock participant with focus changes and a failed attention check.",
    "paste_heavy": "Local mock participant who pastes substantial text into task responses.",
    "fast_low_effort": "Very short responses and very low latencies.",
    "mock_llm_assisted": "Polished, generic wording with a disclosure probe indicating AI assistance.",
    "browser_agent_like": "Automated-looking local mock with near-zero keydown telemetry.",
}


TASK_RESPONSES = {
    "attentive_human_like": "The move gives the garden more light, so seedlings grow more evenly. The trade-off is that the riverside soil dries faster and volunteers need to water more often.",
    "inattentive": "It was about a garden and people helped.",
    "paste_heavy": "The passage presents a practical trade-off: brighter conditions improve growth, but the riverside setting increases the need for weekend watering because the soil dries out faster.",
    "fast_low_effort": "Good idea but more work.",
    "mock_llm_assisted": "Overall, the scenario illustrates a nuanced balance between improved environmental conditions and increased operational burden, suggesting that the benefits depend on sustained volunteer capacity.",
    "browser_agent_like": "The move improved light exposure while increasing watering demands.",
}


def response_for(profile_label: str, item: dict) -> str:
    item_type = item.get("type", "normal_task")
    if item_type == "attention_check":
        return "green" if profile_label in {"inattentive", "fast_low_effort"} else item["expected_response"]
    if item_type == "comprehension_check":
        if profile_label == "fast_low_effort":
            return "anything"
        return item["expected_response"]
    if item_type == "normal_task":
        return TASK_RESPONSES[profile_label]
    if item["id"] == "probe_strategy":
        if profile_label == "mock_llm_assisted":
            return "I drafted with a writing assistant and then lightly edited the result."
        if profile_label == "browser_agent_like":
            return "Automated form completion used fixed templates."
        return "I read each passage and typed a short answer from the details on the page."
    if item["id"] == "probe_assistance":
        if profile_label == "mock_llm_assisted":
            return "Yes, I used a mock AI assistant in this local simulation."
        if profile_label == "browser_agent_like":
            return "Browser-agent-like local automation generated the answers."
        return "No external assistance."
    if item["id"] == "probe_confidence":
        return "The bike rack answer felt least certain because the passage gave competing constraints."
    raise ValueError(f"Unknown item: {item}")


def iter_items():
    yield from STIMULI["tasks"]
    yield from STIMULI["checks"]
    yield from STIMULI["probes"]


def build_export():
    participants = []
    responses = []
    for participant_index, profile_label in enumerate(PROFILE_LABELS, start=1):
        participant_id = f"P{participant_index:03d}"
        participants.append(
            {
                "participant_id": participant_id,
                "worker_id": f"local-{profile_label}",
                "assignment_id": f"assignment-{participant_index:03d}",
                "profile_label": profile_label,
                "profile_note": PROFILE_NOTES[profile_label],
                "ai_use_acknowledgement": "I will answer without AI assistance and will disclose any outside help.",
                "source": "local_simulation",
            }
        )
        for response_index, item in enumerate(iter_items(), start=1):
            trial_type = item.get("type", "normal_task")
            if item in STIMULI["probes"]:
                trial_type = "open_text_probe"
            response_text = response_for(profile_label, item)
            expected_response = item.get("expected_response")
            check_passed = (
                None
                if expected_response is None
                else response_text.strip().lower() == expected_response.lower()
            )
            telemetry = build_synthetic_telemetry(profile_label, item["id"])
            telemetry["source"] = "local_simulation"
            responses.append(
                {
                    "response_id": f"{participant_id}-R{response_index:02d}",
                    "participant_id": participant_id,
                    "profile_label": profile_label,
                    "page_label": item["id"],
                    "trial_id": item["id"],
                    "trial_type": trial_type,
                    "stimulus_id": item["id"],
                    "stimulus_metadata": item,
                    "answer": {
                        "response_text": response_text,
                        "trial_id": item["id"],
                        "trial_type": trial_type,
                        "stimulus_id": item["id"],
                        "expected_response": expected_response,
                        "check_passed": check_passed,
                    },
                    "metadata": {"telemetry": telemetry},
                    "created_at": utc_now(),
                    "source": "simulated_psynet_format",
                }
            )
    return participants, responses


def write_export(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    participants, responses = build_export()
    (output_dir / "participants.json").write_text(
        json.dumps(participants, indent=2) + "\n", encoding="utf-8"
    )
    with (output_dir / "responses.jsonl").open("w", encoding="utf-8") as f:
        for response in responses:
            f.write(json.dumps(response) + "\n")
    (output_dir / "README.md").write_text(
        "# Simulated PsyNet-format export\n\n"
        "This export is locally generated mock data. It follows PsyNet response "
        "shape closely enough for the review script: participant identifiers, "
        "page/trial labels, answer objects, metadata.telemetry, check outcomes, "
        "and explicit simulated profile labels. It is not private participant "
        "data and it is not evidence of real AI use or platform fraud.\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="simulated_export",
        help="Directory for participants.json and responses.jsonl.",
    )
    args = parser.parse_args()
    write_export(Path(args.output_dir))


if __name__ == "__main__":
    main()
