import json
from pathlib import Path


PROMPTS = [
    {
        "trial_id": "summary_local_food",
        "kind": "normal",
        "stimulus": "A neighborhood group plans a shared dinner using locally grown food.",
    },
    {
        "trial_id": "explain_library",
        "kind": "normal",
        "stimulus": "A public library extends evening hours during exam season.",
    },
    {
        "trial_id": "attention_blue_sky",
        "kind": "attention_check",
        "stimulus": "Attention check: please type the word blue in the response box.",
        "expected_answer": "blue",
    },
]


PROFILES = [
    {
        "participant_id": "P001",
        "worker_id": "local_attentive",
        "profile_label": "attentive_human_like",
        "description": "Typed original responses, normal latencies, passed the check.",
        "responses": [
            "The dinner uses local produce and could work because neighbors share planning.",
            "Students and evening workers benefit because they have more quiet study time.",
            "blue",
        ],
        "latencies": [18500, 22100, 5100],
        "first_key_latencies": [1300, 1500, 900],
        "paste_counts": [0, 0, 0],
        "focus_losses": [0, 0, 0],
        "keydown_factor": 1.0,
        "edit_divisor": 7,
    },
    {
        "participant_id": "P002",
        "worker_id": "local_rushed",
        "profile_label": "rushed_failed_check",
        "description": "Very fast responses, sparse typing telemetry, failed the check.",
        "responses": ["good idea", "helps people", "green"],
        "latencies": [1500, 1700, 1200],
        "first_key_latencies": [120, 140, 100],
        "paste_counts": [0, 0, 0],
        "focus_losses": [1, 0, 0],
        "keydown_factor": 0.45,
        "edit_divisor": 12,
    },
    {
        "participant_id": "P003",
        "worker_id": "local_pasted",
        "profile_label": "pasted_ai_disclosed",
        "description": "Disclosed AI assistance and pasted polished long responses.",
        "responses": [
            "I used an AI tool to draft this. The plan may work because local suppliers and shared volunteer labor reduce friction.",
            "I used an AI tool to draft this. Extended hours benefit students who need quiet space after daytime obligations.",
            "blue",
        ],
        "latencies": [4200, 3900, 2600],
        "first_key_latencies": [3000, 2800, 700],
        "paste_counts": [1, 1, 0],
        "focus_losses": [2, 1, 0],
        "keydown_factor": 0.08,
        "edit_divisor": 20,
        "disclosed_ai_assistance": True,
    },
]


def make_trial(profile, prompt, response_text, latency, first_key_latency, paste_count, focus_loss):
    keydown_count = max(1, int(len(response_text) * profile["keydown_factor"]))
    edit_count = max(1, len(response_text) // profile["edit_divisor"])
    attention_passed = (
        response_text.strip().lower().rstrip(".!") == prompt.get("expected_answer")
        if prompt["kind"] == "attention_check"
        else None
    )
    telemetry = {
        "trial_id": prompt["trial_id"],
        "stimulus_kind": prompt["kind"],
        "stimulus": prompt["stimulus"],
        "participant_id": profile["participant_id"],
        "participant_profile": profile["profile_label"],
        "page_started_at_ms": 0,
        "submitted_at_ms": latency,
        "response_latency_ms": latency,
        "first_key_latency_ms": first_key_latency,
        "keydown_count": keydown_count,
        "edit_count": edit_count,
        "paste_count": paste_count,
        "pasted_character_count": len(response_text) if paste_count else 0,
        "focus_count": 1,
        "blur_count": focus_loss,
        "visibility_hidden_count": focus_loss,
        "max_text_length": len(response_text),
        "inter_key_interval_count": max(0, keydown_count - 1),
        "mean_inter_key_interval_ms": 95 if keydown_count > 5 else None,
        "max_inter_key_interval_ms": 420 if keydown_count > 5 else None,
        "attention_check_passed": attention_passed,
        "directly_recorded": False,
        "simulation_note": "Generated fixture mirroring PsyNet response metadata shape.",
    }
    return {
        "participant_id": profile["participant_id"],
        "worker_id": profile["worker_id"],
        "label": prompt["trial_id"],
        "page_type": "TelemetryTextPage",
        "answer": {
            "response_text": response_text,
            "telemetry": telemetry,
        },
        "metadata": {
            "time_taken": latency / 1000,
            "quality_telemetry": telemetry,
        },
    }


def build_fixture():
    participants = []
    responses = []
    for profile in PROFILES:
        participants.append(
            {
                "participant_id": profile["participant_id"],
                "worker_id": profile["worker_id"],
                "participant_profile": profile["profile_label"],
                "profile_description": profile["description"],
                "disclosed_ai_assistance": profile.get("disclosed_ai_assistance", False),
            }
        )
        for prompt, response_text, latency, first_key_latency, paste_count, focus_loss in zip(
            PROMPTS,
            profile["responses"],
            profile["latencies"],
            profile["first_key_latencies"],
            profile["paste_counts"],
            profile["focus_losses"],
            strict=True,
        ):
            responses.append(
                make_trial(
                    profile,
                    prompt,
                    response_text,
                    latency,
                    first_key_latency,
                    paste_count,
                    focus_loss,
                )
            )
    return {
        "schema": "psynet_quality_telemetry_fixture_v1",
        "source": "local simulated participants; no private participant data",
        "participants": participants,
        "responses": responses,
    }


def main():
    output = Path("../../evidence/psynet_quality_fixture.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_fixture(), indent=2) + "\n")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
