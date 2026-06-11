import os

import pytest

from score_telemetry import score_export
from simulate_profiles import build_export


pytest_plugins = ["pytest_dallinger", "pytest_psynet"]
experiment_dir = os.path.dirname(__file__)


@pytest.mark.parametrize("experiment_directory", [experiment_dir], indirect=True)
def test_experiment(launched_experiment):
    launched_experiment.test_experiment()


def test_review_scoring_flags_only_suspicious_profiles():
    export = build_export()
    scored = {row["participant_id"]: row for row in score_export(export)}

    assert scored["P001"]["review_decision"] == "no_review_flag"
    assert scored["P002"]["review_decision"] == "manual_review"
    assert "fast_median_latency" in scored["P002"]["signals"]
    assert "low_response_variance" in scored["P002"]["signals"]
    assert scored["P003"]["review_decision"] == "manual_review"
    assert "attention_check_failed" in scored["P003"]["signals"]
    assert scored["P004"]["review_decision"] == "manual_review"
    assert "response_consistency_mismatch" in scored["P004"]["signals"]
    assert scored["P005"]["review_decision"] == "manual_review"
    assert "missing_timing_telemetry" in scored["P005"]["signals"]
    assert all("proof" not in row["interpretation"].lower() for row in scored.values())
