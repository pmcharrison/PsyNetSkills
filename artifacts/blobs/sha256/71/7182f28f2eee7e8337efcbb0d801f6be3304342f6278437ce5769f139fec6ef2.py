from pathlib import Path

from review_participants import review_export
from simulate_export import write_export


def test_simulated_profiles_produce_conservative_review_flags(tmp_path: Path):
    export_dir = tmp_path / "export"
    write_export(export_dir)

    rows = review_export(export_dir)
    by_profile = {row["profile_label"]: row for row in rows}

    assert by_profile["attentive_human_like"]["flag_for_manual_review"] is False
    assert by_profile["inattentive"]["failed_check_count"] >= 1
    assert by_profile["paste_heavy"]["paste_total"] >= 2
    assert by_profile["fast_low_effort"]["very_short_latency_count"] >= 2
    assert by_profile["mock_llm_assisted"]["generic_probe_count"] >= 1
    assert by_profile["browser_agent_like"]["sparse_text_production_count"] >= 1
    assert all("prove" not in row["review_language"].lower() for row in rows)
