def test_trial_count():
    import experiment

    assert experiment.TOTAL_TRIALS == 50
    assert len(experiment.DESIGN_METADATA["validities"]) == 5
