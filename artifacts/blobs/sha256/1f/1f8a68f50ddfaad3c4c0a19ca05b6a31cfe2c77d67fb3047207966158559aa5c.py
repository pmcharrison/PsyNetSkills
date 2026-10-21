from adaptive import Observation, choose_length, response_probability, y_from_answer


def test_exact_answer_mapping():
    assert y_from_answer("1234", "1234") == 1
    assert y_from_answer("1234 ", "1234") == 1
    assert y_from_answer("1235", "1234") == 0


def test_response_probability_declines_with_length():
    assert response_probability(2, 1.0) > response_probability(20, 1.0)


def test_adaptive_decision_has_export_metadata():
    observations = [
        Observation("p1", 4, 1),
        Observation("p1", 8, 1),
        Observation("p1", 14, 0),
    ]
    decision = choose_length(observations, "p1", seed=123)
    metadata = decision.to_definition_metadata()
    assert 2 <= decision.selected_length <= 20
    assert metadata["posterior_snapshot_id"]
    assert len(metadata["candidate_acquisition_values"]) == 19
    assert len(metadata["posterior_predictive_y"]) == 2
    assert metadata["timing_ms"]["total"] > 0
