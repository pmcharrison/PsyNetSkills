import argparse
import json
from collections import defaultdict
from pathlib import Path


RULES = {
    "failed_attention_check": "Attention/comprehension check answer did not match the expected answer.",
    "very_fast_response": "Normal text response latency was below 3 seconds.",
    "short_response": "Normal text response was shorter than 20 characters.",
    "paste_activity": "Pasted text appeared in an open-text response.",
    "focus_or_visibility_loss": "The browser lost focus or visibility during a response page.",
    "sparse_keydown_telemetry": "Keydown count was low relative to final response length.",
    "short_first_key_latency": "First keypress happened within 250 ms of page load.",
    "ai_disclosure": "Participant disclosed AI assistance in local fixture metadata.",
}


def load_fixture(path):
    return json.loads(Path(path).read_text())


def response_flags(response):
    flags = []
    answer = response["answer"]["response_text"]
    telemetry = response["metadata"]["quality_telemetry"]
    if telemetry["attention_check_passed"] is False:
        flags.append("failed_attention_check")
    if telemetry["stimulus_kind"] == "normal" and telemetry["response_latency_ms"] < 3000:
        flags.append("very_fast_response")
    if telemetry["stimulus_kind"] == "normal" and len(answer.strip()) < 20:
        flags.append("short_response")
    if telemetry["paste_count"] > 0 or telemetry["pasted_character_count"] > 0:
        flags.append("paste_activity")
    if telemetry["blur_count"] > 0 or telemetry["visibility_hidden_count"] > 0:
        flags.append("focus_or_visibility_loss")
    if telemetry["stimulus_kind"] == "normal" and telemetry["keydown_count"] < max(5, len(answer) * 0.25):
        flags.append("sparse_keydown_telemetry")
    if telemetry["first_key_latency_ms"] is not None and telemetry["first_key_latency_ms"] < 250:
        flags.append("short_first_key_latency")
    return flags


def review(data):
    participants = {
        participant["participant_id"]: participant for participant in data["participants"]
    }
    grouped = defaultdict(list)
    for response in data["responses"]:
        grouped[response["participant_id"]].append(response)

    rows = []
    for participant_id, responses in grouped.items():
        participant = participants[participant_id]
        flags = []
        evidence = []
        if participant.get("disclosed_ai_assistance"):
            flags.append("ai_disclosure")
            evidence.append("fixture profile marks disclosed_ai_assistance=true")
        for response in responses:
            for flag in response_flags(response):
                flags.append(flag)
                telemetry = response["metadata"]["quality_telemetry"]
                evidence.append(
                    f"{response['label']}: {flag} "
                    f"(latency={telemetry['response_latency_ms']}ms, "
                    f"paste={telemetry['paste_count']}, "
                    f"keydown={telemetry['keydown_count']}, "
                    f"focus_loss={telemetry['blur_count'] + telemetry['visibility_hidden_count']})"
                )
        unique_flags = sorted(set(flags))
        rows.append(
            {
                "participant_id": participant_id,
                "worker_id": participant["worker_id"],
                "participant_profile": participant["participant_profile"],
                "flag_for_manual_review": bool(unique_flags),
                "review_worthy_signals": unique_flags,
                "evidence": evidence,
                "interpretation": (
                    "Review-worthy signals only; this output does not prove AI use, bot use, fraud, "
                    "or dishonest behavior and must not be used for automatic rejection."
                ),
            }
        )
    return {
        "rules": RULES,
        "participants": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to psynet_quality_fixture.json")
    parser.add_argument("--output", required=True, help="Path for participant review JSON")
    args = parser.parse_args()
    result = review(load_fixture(args.input))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("Manual-review thresholds:")
    for key, description in RULES.items():
        print(f"- {key}: {description}")
    for row in result["participants"]:
        status = "FLAG FOR MANUAL REVIEW" if row["flag_for_manual_review"] else "no review flag"
        signals = ", ".join(row["review_worthy_signals"]) or "none"
        print(f"{row['participant_id']} ({row['participant_profile']}): {status}; signals={signals}")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
