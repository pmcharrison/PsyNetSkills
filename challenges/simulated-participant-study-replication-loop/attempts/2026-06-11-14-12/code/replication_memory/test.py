from experiment import WORD_PAIRS, Exp


def test_stimulus_manifest_is_balanced():
    conditions = [trial["condition"] for trial in WORD_PAIRS]
    assert conditions.count("literal") == conditions.count("interference") == 4
    assert len({trial["pair_id"] for trial in WORD_PAIRS}) == len(WORD_PAIRS)


def test_experiment_has_expected_bot_count():
    assert Exp.test_n_bots == 4
